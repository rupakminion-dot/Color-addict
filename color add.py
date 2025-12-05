import pygame
import random
import sys
from collections import deque

SCREEN_W, SCREEN_H = 1100, 700
FPS = 60
YELLOW_BG = (255, 210, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (40, 40, 40)
GREY = (150, 150, 150)

COLOR_NAMES = [
    "black", "brown", "grey", "red", "orange",
    "yellow", "blue", "purple", "pink", "green"
]

COLOR_MAP = {
    "black": (0, 0, 0),
    "brown": (120, 72, 0),
    "grey": (120, 120, 120),
    "red": (220, 40, 40),
    "orange": (255, 140, 0),
    "yellow": (240, 210, 0),
    "blue": (40, 100, 220),
    "purple": (130, 60, 180),
    "pink": (240, 120, 180),
    "green": (40, 160, 80),
}

CARD_W, CARD_H = 140, 80
CARD_MARGIN = 15

CENTER_COLS = 1   
CENTER_Y = 280

PLAYER_AREA_Y = SCREEN_H - 250
AI_AREA_Y = 70

DRAW_BTN_RECT = pygame.Rect(30, SCREEN_H - 70, 150, 40)

COMPUTER_REACTION_MS = 2000  


def make_card(text_color_name, ink_color_name):

    splashes = []
    for _ in range(5):
        r = random.randint(8, 20)
        x = random.randint(10, CARD_W - 10)
        y = random.randint(10, CARD_H - 10)
        c = random.choice(list(COLOR_MAP.values()))
        splashes.append((x, y, r, c))
    return {"text": text_color_name, "ink": ink_color_name, "splashes": splashes}

def random_card():
    t = random.choice(COLOR_NAMES)
    i = random.choice(COLOR_NAMES)
    return make_card(t, i)

def card_matches(card, center_card):
    return (
        card["text"] == center_card["text"] or
        card["ink"] == center_card["ink"] or
        card["text"] == center_card["ink"] or
        card["ink"] == center_card["text"]
    )



def draw_button(surface, rect, text, font, bg, fg=BLACK, border=BLACK, border_w=2):
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, width=border_w, border_radius=8)
    ts = font.render(text, True, fg)
    tw, th = ts.get_size()
    surface.blit(ts, (rect.x + (rect.w - tw)//2, rect.y + (rect.h - th)//2))

def draw_card(surface, rect, card, font):
    
    pygame.draw.rect(surface, WHITE, rect, border_radius=10)
    pygame.draw.rect(surface, DARK, rect, width=2, border_radius=10)
    pygame.draw.rect(surface, COLOR_MAP[card["ink"]], rect, width=4, border_radius=10)


    for (x, y, r, c) in card["splashes"]:
        pygame.draw.circle(surface, c, (rect.left + x, rect.top + y), r)

 
    label = card["text"].upper()
    ts = font.render(label, True, COLOR_MAP[card["ink"]])
    tw, th = ts.get_size()
    surface.blit(ts, (rect.x + (rect.w - tw)//2, rect.y + (rect.h - th)//2))

def layout_cards_row(start_x, y, cards, max_per_row=7, gap=CARD_MARGIN):
    rects = []
    x = start_x
    count = 0
    row = 0
    for _ in cards:
        rect = pygame.Rect(x, y + row*(CARD_H + gap), CARD_W, CARD_H)
        rects.append(rect)
        x += CARD_W + gap
        count += 1
        if count % max_per_row == 0:
            x = start_x
            row += 1
    return rects


class Player:
    def __init__(self, name):
        self.name = name
        
        self.draw_pile = deque([random_card() for _ in range(21)])
        
        self.hand = []
        self.draw_to_hand(3)

    def draw_to_hand(self, n=1):
        for _ in range(n):
            if self.draw_pile:
                self.hand.append(self.draw_pile.popleft())

    def playable_indices(self, centers):
        idxs = []
        for i, card in enumerate(self.hand):
            for c in centers:
                if card_matches(card, c):
                    idxs.append(i)
                    break
        return idxs

    def has_won(self):
        return len(self.hand) == 0 and len(self.draw_pile) == 0


class GameState:
    def __init__(self):
      
        self.centers = [random_card() for _ in range(CENTER_COLS)]
        self.player = Player("You")
        self.ai = Player("Computer")
        self.last_ai_action = 0
        self.game_over = False
        self.winner = None

    def play_card_to_center(self, card_index, center_index, by="You"):
        if by == "You":
            card = self.player.hand.pop(card_index)
        else:
            card = self.ai.hand.pop(card_index)
     
        self.centers[center_index] = card
        self.check_win()

    def check_win(self):
        if self.player.has_won():
            self.game_over = True
            self.winner = "You"
        elif self.ai.has_won():
            self.game_over = True
            self.winner = "Computer"

    def ai_try_play(self, now_ms):
        if self.game_over:
            return
       
        if now_ms - self.last_ai_action < COMPUTER_REACTION_MS:
            return
        self.last_ai_action = now_ms

    
        for i, card in enumerate(self.ai.hand):
            for ci, cc in enumerate(self.centers):
                if card_matches(card, cc):
                    self.play_card_to_center(i, ci, by="AI")
                    return

       
        if self.ai.draw_pile:
            self.ai.draw_to_hand(1)




STATE_MENU = "menu"
STATE_RULES = "rules"
STATE_GAME = "game"
STATE_OVER = "over"

def draw_menu(screen, title_font, btn_font):
    screen.fill(YELLOW_BG)
    title = "Colour Addict"
    ts = title_font.render(title, True, BLACK)
    screen.blit(ts, (SCREEN_W//2 - ts.get_width()//2, 80))
    play_rect = pygame.Rect(SCREEN_W//2 - 120, 220, 240, 60)
    rules_rect = pygame.Rect(SCREEN_W//2 - 120, 320, 240, 60)
    draw_button(screen, play_rect, "Play", btn_font, WHITE)
    draw_button(screen, rules_rect, "Rules", btn_font, WHITE)
    return play_rect, rules_rect


def draw_rules(screen, title_font, text_font, btn_font):
    screen.fill(YELLOW_BG)
    ts = title_font.render("Rules", True, BLACK)
    screen.blit(ts, (SCREEN_W//2 - ts.get_width()//2, 40))
    lines = [
        "- Both player and computer have 21 cards.",
        "- One center card is open.",
        "- Match by color or text. Cross-match allowed.",
        "- If you can't play, click DRAW to draw from your pile.",
        "- First to empty all cards wins.",
        "- Computer reacts with 3 sec delay.",
    ]
    y = 120
    for ln in lines:
        rs = text_font.render(ln, True, BLACK)
        screen.blit(rs, (80, y))
        y += rs.get_height() + 8
    back_rect = pygame.Rect(40, SCREEN_H - 80, 180, 50)
    draw_button(screen, back_rect, "Back", btn_font, WHITE)
    return back_rect


def draw_game(screen, fonts, game):
    screen.fill(YELLOW_BG)
    big_font, card_font, small_font = fonts

 
    header = big_font.render("Colour Addict", True, BLACK)
    screen.blit(header, (SCREEN_W//2 - header.get_width()//2, 10))

    
    center_start_x = (SCREEN_W - CARD_W) // 2
    center_rects = []
    for i in range(CENTER_COLS):
        rect = pygame.Rect(center_start_x, CENTER_Y, CARD_W, CARD_H)
        center_rects.append(rect)
        draw_card(screen, rect, game.centers[i], card_font)


    ai_label = small_font.render(
        f"Computer: {len(game.ai.hand)} in hand | {len(game.ai.draw_pile)} in pile", True, BLACK
    )
    screen.blit(ai_label, (30, AI_AREA_Y - 30))
    ai_rects = layout_cards_row(30, AI_AREA_Y, game.ai.hand, max_per_row=8)
    for rect in ai_rects:
        pygame.draw.rect(screen, GREY, rect, border_radius=10)
        pygame.draw.rect(screen, DARK, rect, width=2, border_radius=10)
        q = small_font.render("?", True, BLACK)
        screen.blit(q, (rect.x + rect.w//2 - q.get_width()//2, rect.y + rect.h//2 - q.get_height()//2))

    
    player_label = small_font.render(
        f"You: {len(game.player.hand)} in hand | {len(game.player.draw_pile)} in pile", True, BLACK
    )
    screen.blit(player_label, (30, PLAYER_AREA_Y - 35))
    player_rects = layout_cards_row(30, PLAYER_AREA_Y, game.player.hand, max_per_row=8)
    for rect, card in zip(player_rects, game.player.hand):
        draw_card(screen, rect, card, card_font)

   
    draw_button(screen, DRAW_BTN_RECT, "Draw", small_font, WHITE)

    
    playables = game.player.playable_indices(game.centers)
    hint = small_font.render(f"Playable now: {len(playables)}", True, BLACK)
    screen.blit(hint, (200, SCREEN_H - 65))

    return center_rects, player_rects


def draw_game_over(screen, title_font, text_font, btn_font, winner):
    screen.fill(YELLOW_BG)
    msg = f"{winner} win!" if winner else "Game Over"
    ts = title_font.render(msg, True, BLACK)
    screen.blit(ts, (SCREEN_W//2 - ts.get_width()//2, 200))
    back_rect = pygame.Rect(SCREEN_W//2 - 100, 320, 200, 60)
    draw_button(screen, back_rect, "Main menu", btn_font, WHITE)
    return back_rect




def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Colour Addict")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 48, bold=True)
    card_font = pygame.font.SysFont("arial", 28, bold=True)
    btn_font = pygame.font.SysFont("arial", 28, bold=True)
    text_font = pygame.font.SysFont("arial", 24)

    state = STATE_MENU
    game = None

    while True:
        dt = clock.tick(FPS)
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == STATE_GAME and not game.game_over:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if DRAW_BTN_RECT.collidepoint(mx, my):
                        game.player.draw_to_hand(1)
                    else:
                        center_rects, player_rects = draw_game(screen, (title_font, card_font, text_font), game)
                        for idx, rect in enumerate(player_rects):
                            if rect.collidepoint(mx, my) and idx < len(game.player.hand):
                                selected = game.player.hand[idx]
                                match_index = None
                                for ci, cc in enumerate(game.centers):
                                    if card_matches(selected, cc):
                                        match_index = ci
                                        break
                                if match_index is not None:
                                    game.play_card_to_center(idx, match_index, by="You")
                                break
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game.player.draw_to_hand(1)

    
        if state == STATE_GAME and game and not game.game_over:
            game.ai_try_play(now_ms)

     
        if state == STATE_MENU:
            play_rect, rules_rect = draw_menu(screen, title_font, btn_font)
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if play_rect.collidepoint(mx, my):
                    game = GameState()
                    state = STATE_GAME
                elif rules_rect.collidepoint(mx, my):
                    state = STATE_RULES

        elif state == STATE_RULES:
            back_rect = draw_rules(screen, title_font, text_font, btn_font)
            if pygame.mouse.get_pressed()[0]:
                if back_rect.collidepoint(pygame.mouse.get_pos()):
                    state = STATE_MENU

        elif state == STATE_GAME:
            center_rects, player_rects = draw_game(screen, (title_font, card_font, text_font), game)
            if game.game_over:
                state = STATE_OVER

        elif state == STATE_OVER:
            back_rect = draw_game_over(screen, title_font, text_font, btn_font, game.winner if game else None)
            if pygame.mouse.get_pressed()[0]:
                if back_rect.collidepoint(pygame.mouse.get_pos()):
                    state = STATE_MENU
                    game = None

        pygame.display.flip()


if __name__ == "__main__":
    main()


