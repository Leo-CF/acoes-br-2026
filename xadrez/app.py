import math
import os
import random
import shutil
import sys
import threading
import time

import chess
import chess.engine
import pygame

pygame.init()

# ── layout ──────────────────────────────────────────────────────────────────
SQ    = 64
BX, BY = 16, 16
SBX   = BX + SQ * 8 + 16        # sidebar left  (= 544)
SBW   = 180
WIN_W = SBX + SBW + 12          # 736
WIN_H = BY + SQ * 8 + BY        # 544

# ── colors ───────────────────────────────────────────────────────────────────
C = {
    "bg":       (14,  17,  23),
    "sidebar":  (22,  27,  34),
    "light":    (240, 217, 181),
    "dark":     (181, 136, 99),
    "sel":      (123, 201, 126),
    "check_sq": (230, 57,  70),
    "last":     (205, 209, 110),
    "fg":       (255, 255, 255),
    "hint":     (136, 136, 136),
    "red":      (230, 57,  70),
    "red_hov":  (192, 57,  43),
    "neu":      (30,  34,  42),
    "neu_hov":  (46,  51,  64),
    "gold":     (255, 200,  50),
    "green":    (46,  160,  67),
    "green_hov":(34,  120,  50),
}

SYMS = {
    (chess.WHITE, chess.KING):   "♔", (chess.WHITE, chess.QUEEN):  "♕",
    (chess.WHITE, chess.ROOK):   "♖", (chess.WHITE, chess.BISHOP): "♗",
    (chess.WHITE, chess.KNIGHT): "♘", (chess.WHITE, chess.PAWN):   "♙",
    (chess.BLACK, chess.KING):   "♚", (chess.BLACK, chess.QUEEN):  "♛",
    (chess.BLACK, chess.ROOK):   "♜", (chess.BLACK, chess.BISHOP): "♝",
    (chess.BLACK, chess.KNIGHT): "♞", (chess.BLACK, chess.PAWN):   "♟",
}


def _font(names, size, bold=False):
    for name in names:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    return pygame.font.Font(None, size)


# ── AI: negamax + alpha-beta + piece-square tables ───────────────────────────

PIECE_VAL = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN:  900, chess.KING:     0,
}

# Indexed a1=0 … h8=63  (rank-1 first, matches python-chess square numbers)
PAWN_PST = (
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
)
KNIGHT_PST = (
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
)
BISHOP_PST = (
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
)
ROOK_PST = (
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
)
QUEEN_PST = (
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
)
KING_PST = (
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
)
_PST = {
    chess.PAWN: PAWN_PST, chess.KNIGHT: KNIGHT_PST, chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST, chess.QUEEN:  QUEEN_PST,  chess.KING:   KING_PST,
}


def _pst(pt, sq, color):
    t = _PST[pt]
    return t[sq] if color == chess.WHITE else t[chess.square_mirror(sq)]


def _evaluate(board):
    score = 0
    for pt, val in PIECE_VAL.items():
        for sq in board.pieces(pt, chess.WHITE):
            score += val + _pst(pt, sq, chess.WHITE)
        for sq in board.pieces(pt, chess.BLACK):
            score -= val + _pst(pt, sq, chess.BLACK)
    return score if board.turn == chess.WHITE else -score


def _order(board):
    caps, rest = [], []
    for m in board.legal_moves:
        (caps if board.is_capture(m) else rest).append(m)
    return caps + rest


def _negamax(board, depth, alpha, beta):
    if board.is_game_over():
        return -30000 if board.is_checkmate() else 0
    if depth == 0:
        return _evaluate(board)
    best = -32000
    for m in _order(board):
        board.push(m)
        val = -_negamax(board, depth - 1, -beta, -alpha)
        board.pop()
        if val > best:
            best = val
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best


def compute_ai_move(board, difficulty):
    moves = list(board.legal_moves)
    if not moves:
        return None
    if difficulty == "easy":
        return random.choice(moves)
    depth = 2 if difficulty == "medium" else 4
    best_move, best_val = None, -32000
    for m in _order(board):
        board.push(m)
        val = -_negamax(board, depth - 1, -32000, 32000)
        board.pop()
        if val > best_val:
            best_val, best_move = val, m
    return best_move or random.choice(moves)


# ── app ──────────────────────────────────────────────────────────────────────

class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Xadrez")
        self.clock = pygame.time.Clock()

        chess_names = ["segoeuisymbol", "seguisymbol", "arialunicodems"]
        ui_names    = ["segoui", "segoeui", "calibri", "arial"]
        self.pf = _font(chess_names, 42)
        self.sf = _font(chess_names, 18)
        self.uf = _font(ui_names, 14)
        self.ub = _font(ui_names, 14, True)
        self.lf = _font(ui_names, 11)
        self.tf = _font(ui_names, 52, True)

        self.state      = "menu"    # "menu" | "difficulty" | "game"
        self.mode       = "pvp"     # "pvp" | "cpu"
        self.difficulty = "medium"  # "easy" | "medium" | "hard"
        self.asset      = "classic"  # "pixel" | "classic"
        self.player_col = chess.WHITE

        self.board       = chess.Board()
        self.sel_sq      = None     # selected chess.Square
        self.valid_sqs   = []       # valid destination squares
        self.promoting   = None     # to-square while awaiting promo choice
        self._promo_from = None     # from-square of promoting pawn
        self._status     = "playing"

        self._ai_move      = None
        self._ai_thinking  = False
        self._ai_gen       = 0      # increments on new game; prevents stale moves
        self._history      = []     # list of SAN strings, one per half-move

        self._engine       = None
        self._engine_ok    = False
        self._analysis_on  = False
        self._eval_cp      = 0      # centipawns from white's perspective; ±30000 = mate
        self._best_move    = None   # chess.Move from latest Stockfish analysis
        self._analysis_gen = 0
        self._init_engine()

        self._anim  = None          # current move animation, or None
        self._muted = False
        self._build_sounds()
        self._load_sprites()

    # ── main loop ─────────────────────────────────────────────────────────
    def run(self):
        while True:
            mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self._engine:
                        try: self._engine.quit()
                        except Exception: pass
                    pygame.quit()
                    sys.exit()
                self._handle(event, mouse)

            # Apply ready AI move
            if self.state == "game" and self._ai_move is not None and not self._ai_thinking:
                self._apply_move(self._ai_move)
                self._ai_move = None

            # Trigger AI if it's CPU's turn
            if (self.state == "game" and self.mode == "cpu"
                    and self.board.turn != self.player_col
                    and not self._ai_thinking and self._ai_move is None
                    and not self.board.is_game_over() and self.promoting is None):
                self._start_ai()

            self.screen.fill(C["bg"])
            self._draw(mouse)
            pygame.display.flip()
            self.clock.tick(60)

    # ── event handling ────────────────────────────────────────────────────
    def _handle(self, event, mouse):
        click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

        if self.state == "menu":
            if click and self._r("asset_pixel").collidepoint(mouse):
                self.asset = "pixel";   self._apply_asset()
            elif click and self._r("asset_classic").collidepoint(mouse):
                self.asset = "classic"; self._apply_asset()
            elif click and self._r("pvp").collidepoint(mouse):
                self.mode = "pvp"
                self._new_game()
            elif click and self._r("cpu").collidepoint(mouse):
                self.mode = "cpu"
                self.state = "difficulty"

        elif self.state == "difficulty":
            for diff in ("easy", "medium", "hard"):
                if click and self._r(diff).collidepoint(mouse):
                    self.difficulty = diff
                    self._new_game()
                    return
            if click and self._r("back").collidepoint(mouse):
                self.state = "menu"

        elif self.state == "game":
            if self.promoting:
                if click:
                    for pt, rect in self._promo_rects().items():
                        if rect.collidepoint(mouse):
                            move     = chess.Move(self._promo_from, self.promoting, promotion=pt)
                            piece    = self.board.piece_at(self._promo_from)
                            captured = self.board.piece_at(self.promoting)
                            self._history.append(self.board.san(move))
                            self.board.push(move)
                            self.promoting   = None
                            self._promo_from = None
                            self._status = self._get_status()
                            self._request_analysis()
                            self._start_move_anim(move, piece, None, None)
                            self._play_move_sound(captured)
                            break
                return

            if click and self._r("undo").collidepoint(mouse):
                self._undo()
                return
            if click and self._r("new").collidepoint(mouse):
                self._new_game()
                return
            if click and self._r("menu_btn").collidepoint(mouse):
                self.state = "menu"
                return
            if click and self._r("stockfish_btn").collidepoint(mouse):
                self._toggle_analysis()
                return
            if click and self._r("mute_btn").collidepoint(mouse):
                self._muted = not self._muted
                return


            # Board click only on human's turn (and not while animating)
            cpu_turn = self.mode == "cpu" and self.board.turn != self.player_col
            if click and not cpu_turn and not self._ai_thinking and self._anim is None:
                self._board_click(mouse)

    def _new_game(self):
        self._ai_gen += 1
        self.board.reset()
        self.sel_sq      = None
        self.valid_sqs   = []
        self.promoting   = self._promo_from = None
        self._status     = "playing"
        self._ai_move    = None
        self._ai_thinking = False
        self._history    = []
        self._eval_cp    = 0
        self._best_move  = None
        self._anim       = None
        self.state       = "game"
        self._request_analysis()

    def _board_click(self, mouse):
        if self._status in ("checkmate", "stalemate", "draw"):
            return
        col = (mouse[0] - BX) // SQ
        row = (mouse[1] - BY) // SQ
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        sq    = chess.square(col, 7 - row)
        piece = self.board.piece_at(sq)

        if self.sel_sq is not None:
            if sq in self.valid_sqs:
                self._try_move(self.sel_sq, sq)
                self.sel_sq = None
                self.valid_sqs = []
                return
            if piece and piece.color == self.board.turn:
                self.sel_sq    = sq
                self.valid_sqs = self._legal_tos(sq)
                return
            self.sel_sq = None
            self.valid_sqs = []
            return

        if piece and piece.color == self.board.turn:
            self.sel_sq    = sq
            self.valid_sqs = self._legal_tos(sq)

    def _legal_tos(self, from_sq):
        seen, result = set(), []
        for m in self.board.legal_moves:
            if m.from_square == from_sq and m.to_square not in seen:
                seen.add(m.to_square)
                result.append(m.to_square)
        return result

    def _try_move(self, from_sq, to_sq):
        p = self.board.piece_at(from_sq)
        if p and p.piece_type == chess.PAWN and chess.square_rank(to_sq) in (0, 7):
            self.promoting   = to_sq
            self._promo_from = from_sq
        else:
            self._apply_move(chess.Move(from_sq, to_sq))

    def _apply_move(self, move):
        self._history.append(self.board.san(move))  # SAN must be read before push
        piece = self.board.piece_at(move.from_square)
        if self.board.is_en_passant(move):
            ep_sq    = chess.square(chess.square_file(move.to_square),
                                    chess.square_rank(move.from_square))
            captured = self.board.piece_at(ep_sq)
        else:
            ep_sq    = None
            captured = self.board.piece_at(move.to_square)
        self.board.push(move)
        self.sel_sq    = None
        self.valid_sqs = []
        self._status   = self._get_status()
        self._request_analysis()
        self._start_move_anim(move, piece, captured, ep_sq)
        self._play_move_sound(captured)

    def _get_status(self):
        if self.board.is_checkmate():             return "checkmate"
        if self.board.is_stalemate():             return "stalemate"
        if self.board.is_insufficient_material(): return "draw"
        if self.board.is_check():                 return "check"
        return "playing"

    def _undo(self):
        if self._ai_thinking:
            return
        # CPU mode: need to undo the pair (player + CPU) to keep it the player's turn
        if self.mode == "cpu":
            if len(self.board.move_stack) < 2:
                return
            self.board.pop()
            self.board.pop()
            for _ in range(2):
                if self._history: self._history.pop()
        else:
            if not self.board.move_stack:
                return
            self.board.pop()
            if self._history: self._history.pop()
        self.sel_sq    = None
        self.valid_sqs = []
        self.promoting = self._promo_from = None
        self._ai_move  = None
        self._anim     = None
        self._ai_gen  += 1   # discard any in-flight CPU move
        self._status   = self._get_status()
        self._request_analysis()

    def _start_move_anim(self, move, piece, captured, ep_sq):
        self._anim = {
            "from_sq":  move.from_square,
            "to_sq":    move.to_square,
            "piece":    piece,
            "captured": captured,
            "cap_sq":   ep_sq if ep_sq is not None else move.to_square,
            "start":    time.monotonic(),
            "dur":      0.18,
        }

    # ── sounds ───────────────────────────────────────────────────────────
    def _gen_seq(self, notes, sr=44100):
        import array as _arr
        buf = _arr.array('h')
        for freq, dur, vol in notes:
            n    = int(sr * dur)
            fade = max(1, min(int(sr * 0.015), n // 3))
            for i in range(n):
                if i < fade:           env = i / fade
                elif i > n - fade:     env = (n - i) / fade
                else:                  env = 1.0
                if freq > 0:
                    s = int(32767 * vol * env * math.sin(2 * math.pi * freq * i / sr))
                else:
                    s = 0
                buf.extend((s, s))   # stereo L+R
        return pygame.mixer.Sound(buffer=buf)

    def _build_sounds(self):
        try:
            self._snd_move     = self._gen_seq([(520, 0.06, 0.35)])
            self._snd_capture  = self._gen_seq([(380, 0.05, 0.55), (240, 0.09, 0.65)])
            self._snd_check    = self._gen_seq([(660, 0.06, 0.45), (0, 0.03, 0),
                                                (880, 0.09, 0.50)])
            self._snd_gameover = self._gen_seq([(523, 0.13, 0.50), (0, 0.02, 0),
                                                (440, 0.13, 0.45), (0, 0.02, 0),
                                                (330, 0.22, 0.55)])
        except Exception:
            self._snd_move = self._snd_capture = self._snd_check = self._snd_gameover = None

    def _load_sprites(self):
        if getattr(sys, "frozen", False):
            root = sys._MEIPASS
        else:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._asset_packs = {}
        for name, loader in [("pixel", self._load_pixel_pack),
                              ("classic", self._load_classic_pack)]:
            try:
                self._asset_packs[name] = loader(root)
            except Exception:
                self._asset_packs[name] = {"sprites": {}, "board": None}
        self._apply_asset()

    def _load_pixel_pack(self, root):
        PIECE_FILES = {
            chess.KING:   "chess-king",   chess.QUEEN:  "chess-queen",
            chess.ROOK:   "chess-rook",   chess.BISHOP: "chess-bishop",
            chess.KNIGHT: "chess-knight", chess.PAWN:   "chess-pawn",
        }
        base    = os.path.join(root, "Chess_asset")
        sprites = {}
        for pt, name in PIECE_FILES.items():
            for color, suffix in [(chess.WHITE, "white"), (chess.BLACK, "black")]:
                img = pygame.image.load(
                    os.path.join(base, f"{name}-{suffix}.png")).convert_alpha()
                sprites[(color, pt)] = pygame.transform.smoothscale(img, (SQ, SQ))
        board_raw = pygame.image.load(os.path.join(base, "board.png")).convert()
        return {"sprites": sprites,
                "board": pygame.transform.smoothscale(board_raw, (SQ * 8, SQ * 8))}

    def _load_classic_pack(self, _root):
        return {"sprites": {}, "board": None}

    def _apply_asset(self):
        pack            = self._asset_packs.get(self.asset, {})
        self._sprites   = pack.get("sprites", {})
        self._board_img = pack.get("board", None)

    def _play_move_sound(self, captured):
        if self._muted:
            return
        if self._status in ("checkmate", "stalemate", "draw"):
            snd = self._snd_gameover
        elif self._status == "check":
            snd = self._snd_check
        elif captured:
            snd = self._snd_capture
        else:
            snd = self._snd_move
        if snd:
            snd.play()

    # ── AI ────────────────────────────────────────────────────────────────
    def _start_ai(self):
        self._ai_thinking = True
        board_copy = self.board.copy()
        diff       = self.difficulty
        gen        = self._ai_gen

        def think():
            t0   = time.monotonic()
            move = compute_ai_move(board_copy, diff)
            remaining = 1.0 - (time.monotonic() - t0)
            if remaining > 0:
                time.sleep(remaining)
            if self._ai_gen == gen:
                self._ai_move = move
            self._ai_thinking = False

        threading.Thread(target=think, daemon=True).start()

    def _init_engine(self):
        candidates = []
        if getattr(sys, "frozen", False):
            for _sf in ("stockfish.exe", "stockfish-windows-x86-64-avx2.exe"):
                candidates.append(os.path.join(sys._MEIPASS, _sf))
        candidates.append("stockfish")
        for p in [
            r"C:\stockfish\stockfish-windows-x86-64-avx2.exe",
            r"C:\stockfish\stockfish-windows-x86-64.exe",
            r"C:\stockfish\stockfish.exe",
            r"C:\Program Files\Stockfish\stockfish.exe",
            r"C:\Program Files (x86)\Stockfish\stockfish.exe",
        ]:
            candidates.append(p)
        for c in candidates:
            if shutil.which(c) is None and not os.path.isfile(c):
                continue
            try:
                self._engine = chess.engine.SimpleEngine.popen_uci(c)
                self._engine_ok = True
                return
            except Exception:
                pass

    def _toggle_analysis(self):
        if not self._engine_ok:
            return
        self._analysis_on = not self._analysis_on
        if self._analysis_on:
            self._request_analysis()
        else:
            self._eval_cp   = 0
            self._best_move = None

    def _request_analysis(self):
        if not self._engine_ok or not self._analysis_on:
            return
        if self.board.is_game_over():
            self._eval_cp   = 0
            self._best_move = None
            return
        self._analysis_gen += 1
        gen        = self._analysis_gen
        board_copy = self.board.copy()

        def analyse():
            try:
                info  = self._engine.analyse(board_copy, chess.engine.Limit(time=0.3))
                if self._analysis_gen != gen:
                    return
                score = info["score"].white()
                if score.is_mate():
                    m = score.mate()
                    self._eval_cp = 30000 if m > 0 else -30000
                else:
                    self._eval_cp = score.score() or 0
                self._best_move = info.get("pv", [None])[0]
            except Exception:
                pass

        threading.Thread(target=analyse, daemon=True).start()

    # ── button rects ──────────────────────────────────────────────────────
    def _r(self, name):
        cx    = WIN_W // 2
        sb_cx = SBX + SBW // 2
        table = {
            # menu
            "pvp":           (cx - 130, WIN_H // 2 - 20,  260, 50),
            "cpu":           (cx - 130, WIN_H // 2 + 40,  260, 50),
            "asset_pixel":   (cx - 130, WIN_H // 2 + 120, 124, 36),
            "asset_classic": (cx + 6,   WIN_H // 2 + 120, 124, 36),
            # difficulty
            "easy":     (cx - 110, WIN_H // 2 - 58, 220, 44),
            "medium":   (cx - 110, WIN_H // 2 -  4, 220, 44),
            "hard":     (cx - 110, WIN_H // 2 + 50, 220, 44),
            "back":     (cx - 110, WIN_H // 2 + 116, 220, 36),
            # game sidebar (5 buttons stacked 44px apart from bottom)
            "mute_btn":      (sb_cx - 70, BY + SQ * 8 - 228, 140, 36),
            "stockfish_btn": (sb_cx - 70, BY + SQ * 8 - 184, 140, 36),
            "undo":          (sb_cx - 70, BY + SQ * 8 - 140, 140, 36),
            "new":           (sb_cx - 70, BY + SQ * 8 -  96, 140, 36),
            "menu_btn":      (sb_cx - 70, BY + SQ * 8 -  52, 140, 36),
        }
        return pygame.Rect(table[name])

    def _promo_rects(self):
        bsz, gap = 82, 8
        pw  = 4 * bsz + 3 * gap + 32
        px  = (WIN_W - pw) // 2
        py  = (WIN_H - 148) // 2
        return {pt: pygame.Rect(px + 16 + i * (bsz + gap), py + 46, bsz, bsz)
                for i, pt in enumerate([chess.QUEEN, chess.ROOK,
                                        chess.BISHOP, chess.KNIGHT])}

    # ── drawing ───────────────────────────────────────────────────────────
    def _draw(self, mouse):
        if self.state == "menu":
            self._draw_menu(mouse)
        elif self.state == "difficulty":
            self._draw_difficulty(mouse)
        else:
            self._draw_board()
            if self._analysis_on and self._best_move and not self.board.is_game_over():
                self._draw_arrow(self._best_move.from_square, self._best_move.to_square)
            self._draw_sidebar(mouse)
            if self.promoting:
                self._draw_promo(mouse)

    def _draw_menu(self, mouse):
        t = self.tf.render("Xadrez", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 - 82)))

        dec = self.sf.render("♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜", True, (55, 62, 75))
        self.screen.blit(dec, dec.get_rect(center=(WIN_W // 2, WIN_H // 2 - 36)))

        sub = self.lf.render("escolha o modo de jogo", True, C["hint"])
        self.screen.blit(sub, sub.get_rect(center=(WIN_W // 2, WIN_H // 2 - 8)))

        self._btn(self._r("pvp"), "Jogador vs Jogador", mouse, C["neu"], C["neu_hov"])
        self._btn(self._r("cpu"), "Jogador vs CPU",     mouse, C["red"], C["red_hov"])

        lbl = self.lf.render("Visual:", True, C["hint"])
        self.screen.blit(lbl, lbl.get_rect(center=(WIN_W // 2, WIN_H // 2 + 107)))
        for key, label in [("asset_pixel", "Pixel Art"), ("asset_classic", "Classic")]:
            active = self.asset == key.replace("asset_", "")
            self._btn(self._r(key), label, mouse,
                      C["green"]     if active else C["neu"],
                      C["green_hov"] if active else C["neu_hov"])

    def _draw_difficulty(self, mouse):
        t = self.ub.render("Escolha a dificuldade", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(WIN_W // 2, WIN_H // 2 - 96)))

        sub = self.lf.render("voce joga com as Brancas", True, C["hint"])
        self.screen.blit(sub, sub.get_rect(center=(WIN_W // 2, WIN_H // 2 - 76)))

        diff_cfg = [
            ("easy",   "Facil",   "movimentos aleatorios"),
            ("medium", "Medio",   "minimax profundidade 2"),
            ("hard",   "Dificil", "minimax profundidade 4"),
        ]
        for key, label, desc in diff_cfg:
            r = self._r(key)
            hov = r.collidepoint(mouse)
            pygame.draw.rect(self.screen, C["neu_hov"] if hov else C["neu"],
                             r, border_radius=8)
            ls = self.ub.render(label, True, C["fg"])
            ds = self.lf.render(desc,  True, C["hint"])
            self.screen.blit(ls, ls.get_rect(midleft=(r.x + 16, r.centery - 7)))
            self.screen.blit(ds, ds.get_rect(midleft=(r.x + 16, r.centery + 9)))

        self._btn(self._r("back"), "< Voltar", mouse, C["neu"], C["neu_hov"])

    def _draw_board(self):
        board    = self.board
        last     = board.peek() if board.move_stack else None
        last_sqs = {last.from_square, last.to_square} if last else set()

        # ── advance animation ─────────────────────────────────────────────────
        anim = self._anim
        t    = 0.0
        if anim:
            raw = min((time.monotonic() - anim["start"]) / anim["dur"], 1.0)
            t   = raw * raw * (3 - 2 * raw)
            if raw >= 1.0:
                self._anim = None
                anim       = None

        # ── board image (or fallback to colored squares) ──────────────────────
        if self._board_img:
            self.screen.blit(self._board_img, (BX, BY))
        else:
            for r in range(8):
                for c in range(8):
                    color = C["light"] if (r + c) % 2 == 0 else C["dark"]
                    pygame.draw.rect(self.screen, color, (BX + c*SQ, BY + r*SQ, SQ, SQ))

        # ── square overlays (semi-transparent) ───────────────────────────────
        ov = pygame.Surface((SQ, SQ), pygame.SRCALPHA)

        for sq in last_sqs:
            c = chess.square_file(sq);  r = 7 - chess.square_rank(sq)
            ov.fill((205, 209, 110, 100))
            self.screen.blit(ov, (BX + c * SQ, BY + r * SQ))

        if self.sel_sq is not None:
            c = chess.square_file(self.sel_sq);  r = 7 - chess.square_rank(self.sel_sq)
            ov.fill((123, 201, 126, 150))
            self.screen.blit(ov, (BX + c * SQ, BY + r * SQ))

        if self._status in ("check", "checkmate"):
            ksq = board.king(board.turn)
            if ksq is not None:
                kc    = chess.square_file(ksq);  kr = 7 - chess.square_rank(ksq)
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 180.0)
                ov.fill((230, 57, 70, int(190 * pulse)))
                self.screen.blit(ov, (BX + kc * SQ, BY + kr * SQ))

        # ── valid-move hints ──────────────────────────────────────────────────
        for sq in self.valid_sqs:
            c   = chess.square_file(sq);  r = 7 - chess.square_rank(sq)
            cx_ = BX + c * SQ + SQ // 2;  cy_ = BY + r * SQ + SQ // 2
            if board.piece_at(sq):
                pygame.draw.circle(self.screen, C["sel"], (cx_, cy_), SQ // 2 - 3, 4)
            else:
                pygame.draw.circle(self.screen, C["sel"], (cx_, cy_), 9)

        # ── captured piece fading out ─────────────────────────────────────────
        if anim and anim["captured"]:
            cc = chess.square_file(anim["cap_sq"]);  cr = 7 - chess.square_rank(anim["cap_sq"])
            self._draw_piece_alpha(anim["captured"],
                                   BX + cc * SQ + SQ // 2,
                                   BY + cr * SQ + SQ // 2,
                                   int(255 * (1.0 - t)))

        # ── static pieces ─────────────────────────────────────────────────────
        skip = anim["to_sq"] if anim else -1
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r)
                if sq == skip:
                    continue
                p = board.piece_at(sq)
                if p:
                    self._draw_piece(p, BX + c * SQ + SQ // 2, BY + r * SQ + SQ // 2)

        # ── moving piece at interpolated position ─────────────────────────────
        if anim:
            fc  = chess.square_file(anim["from_sq"]);  fr = 7 - chess.square_rank(anim["from_sq"])
            tc  = chess.square_file(anim["to_sq"]);    tr = 7 - chess.square_rank(anim["to_sq"])
            fx  = BX + fc * SQ + SQ // 2;  fy  = BY + fr * SQ + SQ // 2
            tx_ = BX + tc * SQ + SQ // 2;  ty_ = BY + tr * SQ + SQ // 2
            self._draw_piece(anim["piece"],
                             int(fx + (tx_ - fx) * t),
                             int(fy + (ty_ - fy) * t))

        # ── coordinate labels ─────────────────────────────────────────────────
        for c, ltr in enumerate("abcdefgh"):
            col = C["light"] if c % 2 == 0 else C["dark"]
            s   = self.lf.render(ltr, True, col)
            self.screen.blit(s, (BX + (c + 1) * SQ - s.get_width() - 3,
                                 BY + 7 * SQ + SQ - s.get_height() - 3))
        for r in range(8):
            col = C["dark"] if r % 2 == 0 else C["light"]
            s   = self.lf.render(str(8 - r), True, col)
            self.screen.blit(s, (BX + 3, BY + r * SQ + 3))

    def _draw_piece(self, p, cx, cy):
        sprite = self._sprites.get((p.color, p.piece_type))
        if sprite:
            self.screen.blit(sprite, sprite.get_rect(center=(cx, cy)))
        else:
            fill = (255, 255, 255) if p.color == chess.WHITE else ( 17,  17,  17)
            shd  = ( 68,  68,  68) if p.color == chess.WHITE else (153, 153, 153)
            sym  = SYMS[(p.color, p.piece_type)]
            for dx, dy, col in ((1, 2, shd), (0, 0, fill)):
                s = self.pf.render(sym, True, col)
                self.screen.blit(s, s.get_rect(center=(cx + dx, cy + dy)))

    def _draw_piece_alpha(self, p, cx, cy, alpha):
        sprite = self._sprites.get((p.color, p.piece_type))
        if sprite:
            surf = sprite.copy()
            surf.set_alpha(alpha)
            self.screen.blit(surf, surf.get_rect(center=(cx, cy)))
        else:
            fill = (255, 255, 255) if p.color == chess.WHITE else (17, 17, 17)
            sym  = SYMS[(p.color, p.piece_type)]
            surf = self.pf.render(sym, True, fill)
            surf.set_alpha(alpha)
            self.screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def _draw_sidebar(self, mouse):
        pygame.draw.rect(self.screen, C["sidebar"],
                         (SBX, BY, SBW, SQ * 8), border_radius=12)
        cx = SBX + SBW // 2

        t = self.ub.render("Xadrez", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(cx, BY + 28)))


        turn   = self.board.turn
        sym_s  = self.sf.render("♔" if turn == chess.WHITE else "♚", True, C["fg"])
        name_s = self.uf.render("Brancas" if turn == chess.WHITE else "Pretas", True, C["fg"])
        total  = sym_s.get_width() + 6 + name_s.get_width()
        bx     = cx - total // 2
        mid    = BY + 58
        self.screen.blit(sym_s,  (bx, mid - sym_s.get_height() // 2))
        self.screen.blit(name_s, (bx + sym_s.get_width() + 6,
                                  mid - name_s.get_height() // 2))

        if self.mode == "cpu":
            diff_lbl = {"easy": "Facil", "medium": "Medio", "hard": "Dificil"}
            ts = self.lf.render(f"CPU  |  {diff_lbl[self.difficulty]}", True, C["hint"])
            self.screen.blit(ts, ts.get_rect(center=(cx, BY + 78)))

        y_st = BY + 96 if self.mode == "cpu" else BY + 80
        st_map = {
            "check":     ("Xeque!",      C["red"]),
            "checkmate": ("Xeque-mate!", C["red"]),
            "stalemate": ("Empate",      C["hint"]),
            "draw":      ("Empate",      C["hint"]),
        }
        if self._status in st_map:
            txt, clr = st_map[self._status]
            s = self.ub.render(txt, True, clr)
            self.screen.blit(s, s.get_rect(center=(cx, y_st)))

        if self._ai_thinking:
            dots = "." * ((pygame.time.get_ticks() // 400) % 4)
            ts = self.uf.render(f"CPU pensando{dots}", True, C["gold"])
            self.screen.blit(ts, ts.get_rect(center=(cx, y_st + 22)))

        self._draw_history()

        min_moves = 2 if self.mode == "cpu" else 1
        can_undo = len(self.board.move_stack) >= min_moves and not self._ai_thinking
        self._btn(self._r("undo"),     "< Desfazer", mouse,
                  C["neu"] if can_undo else (20, 22, 28),
                  C["neu_hov"] if can_undo else (20, 22, 28))
        self._btn(self._r("new"),      "Reiniciar",  mouse, C["neu"], C["neu_hov"])
        self._btn(self._r("menu_btn"), "< Menu",     mouse, C["neu"], C["neu_hov"])

        if not self._engine_ok:
            sf_lbl, sf_bg, sf_hov = "Stockfish n/d", (20, 22, 28), (20, 22, 28)
        elif self._analysis_on:
            sf_lbl, sf_bg, sf_hov = "Stockfish: ON",  C["green"], C["green_hov"]
        else:
            sf_lbl, sf_bg, sf_hov = "Stockfish: OFF", C["neu"],   C["neu_hov"]
        self._btn(self._r("stockfish_btn"), sf_lbl, mouse, sf_bg, sf_hov)

        if self._muted:
            self._btn(self._r("mute_btn"), "Som: OFF", mouse, (35, 28, 28), (50, 38, 38))
        else:
            self._btn(self._r("mute_btn"), "Som: ON",  mouse, C["neu"], C["neu_hov"])

    def _draw_history(self):
        # box bottom = BY+SQ*8-236 = 292, 8px above mute_btn top at 300
        box = pygame.Rect(SBX + 8, BY + 116, SBW - 16, SQ * 8 - 352)

        pygame.draw.rect(self.screen, (18, 22, 30), box, border_radius=6)

        lf  = self.lf

        # Header: "Historico" left side, eval score right side (if analysis on)
        hdr = lf.render("Historico", True, C["hint"])
        self.screen.blit(hdr, (box.left + 5, box.top + 4))
        if self._analysis_on and self._engine_ok:
            cp = self._eval_cp
            if abs(cp) >= 29000:
                m = (30000 - abs(cp)) + 1
                ev_txt = f"M{m}" if cp > 0 else f"-M{m}"
                ev_col = (220, 220, 220) if cp > 0 else (120, 120, 120)
            else:
                ev_txt = f"{cp/100:+.1f}"
                ev_col = (220, 220, 220) if cp >= 0 else (150, 150, 150)
            ev_s = lf.render(ev_txt, True, ev_col)
            self.screen.blit(ev_s, (box.right - ev_s.get_width() - 5, box.top + 4))

        # thin separator
        pygame.draw.line(self.screen, (40, 46, 56),
                         (box.left + 6, box.top + 20),
                         (box.right - 6, box.top + 20))

        line_h   = 14
        area_top = box.top + 26
        area_h   = box.height - 28
        max_rows = area_h // line_h

        # Group half-moves into (move_num, white_san, black_san) rows
        h = self._history
        pairs = [(i // 2 + 1, h[i], h[i + 1] if i + 1 < len(h) else "")
                 for i in range(0, len(h), 2)]

        visible   = pairs[-max_rows:]
        last_idx  = len(pairs) - 1   # index of the last full row

        # "..." indicator if history is scrolled
        start_idx = len(pairs) - len(visible)
        if start_idx > 0:
            dot_s = lf.render("...", True, C["hint"])
            self.screen.blit(dot_s, (box.left + 6, area_top))
            area_top += line_h

        x_num   = box.left + 4
        x_white = box.left + 26
        x_black = box.left + 88

        for row_i, (num, wh, bl) in enumerate(visible):
            is_last = (start_idx + row_i == last_idx)
            y = area_top + row_i * line_h

            clr_w = C["fg"]    if (is_last and bl == "") else (190, 190, 190)
            clr_b = C["fg"]    if (is_last and bl != "") else (190, 190, 190)

            self.screen.blit(lf.render(f"{num}.", True, (80, 85, 95)), (x_num, y))
            self.screen.blit(lf.render(wh, True, clr_w), (x_white, y))
            if bl:
                self.screen.blit(lf.render(bl, True, clr_b), (x_black, y))

    def _draw_arrow(self, from_sq, to_sq):
        fc, fr = chess.square_file(from_sq), chess.square_rank(from_sq)
        tc, tr = chess.square_file(to_sq),   chess.square_rank(to_sq)
        fx = BX + fc * SQ + SQ // 2
        fy = BY + (7 - fr) * SQ + SQ // 2
        tx = BX + tc * SQ + SQ // 2
        ty = BY + (7 - tr) * SQ + SQ // 2

        dx, dy = tx - fx, ty - fy
        dist   = math.hypot(dx, dy)
        if dist < 1:
            return
        ux, uy    = dx / dist, dy / dist
        head_len  = 20
        shaft_end = (tx - ux * head_len, ty - uy * head_len)
        side_x, side_y = -uy * head_len * 0.55, ux * head_len * 0.55

        color = (255, 170, 0, 160)
        ov    = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        pygame.draw.line(ov, color, (fx, fy), shaft_end, 7)
        pygame.draw.polygon(ov, color, [
            (int(tx), int(ty)),
            (int(shaft_end[0] + side_x), int(shaft_end[1] + side_y)),
            (int(shaft_end[0] - side_x), int(shaft_end[1] - side_y)),
        ])
        self.screen.blit(ov, (0, 0))

    def _draw_promo(self, mouse):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        self.screen.blit(ov, (0, 0))

        rects = self._promo_rects()
        bsz, gap = 82, 8
        pw = 4 * bsz + 3 * gap + 32
        ph = 148
        px = (WIN_W - pw) // 2
        py = (WIN_H - ph) // 2
        pygame.draw.rect(self.screen, C["sidebar"], (px, py, pw, ph), border_radius=12)

        t = self.ub.render("Promover peao para:", True, C["fg"])
        self.screen.blit(t, t.get_rect(center=(px + pw // 2, py + 18)))

        p = self.board.piece_at(self._promo_from)
        color = p.color if p else chess.WHITE
        labels = {chess.QUEEN: "Dama", chess.ROOK: "Torre",
                  chess.BISHOP: "Bispo", chess.KNIGHT: "Cavalo"}
        for pt, rect in rects.items():
            pygame.draw.rect(self.screen,
                             C["neu_hov"] if rect.collidepoint(mouse) else C["neu"],
                             rect, border_radius=8)
            fill  = (255, 255, 255) if color == chess.WHITE else (17, 17, 17)
            sym_s = self.pf.render(SYMS[(color, pt)], True, fill)
            self.screen.blit(sym_s, sym_s.get_rect(center=(rect.centerx, rect.centery - 8)))
            n_s = self.lf.render(labels[pt], True, C["hint"])
            self.screen.blit(n_s, n_s.get_rect(center=(rect.centerx, rect.bottom - 10)))

    def _btn(self, rect, text, mouse, bg, bg_hov, radius=8):
        pygame.draw.rect(self.screen,
                         bg_hov if rect.collidepoint(mouse) else bg,
                         rect, border_radius=radius)
        s = self.uf.render(text, True, C["fg"])
        self.screen.blit(s, s.get_rect(center=rect.center))


if __name__ == "__main__":
    App().run()
