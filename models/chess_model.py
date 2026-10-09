import chess
import chess.pgn
import io
from models.db import query_one, query_all, execute_insert, execute_update

# Piece values for Minimax evaluation
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Positional tables for piece placement evaluation (simplified 8x8 PST from white's perspective)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MID_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

# Famous Grandmaster Auto-Demonstration Games (GoChess Robotic Replay)
FAMOUS_GAMES = {
    "opera": {
        "id": "opera",
        "title": "The Opera Game (Morphy Masterpiece)",
        "event": "Paris Opera House, 1858",
        "white": "Paul Morphy",
        "black": "Duke of Brunswick & Count Isouard",
        "description": "Considered the most elegant attacking and sacrifice game in history. Morphy sacrifices Queen, Rook, and pieces with ruthless geometric harmony.",
        "pgn": "1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0"
    },
    "immortal": {
        "id": "immortal",
        "title": "The Immortal Game (Anderssen vs Kieseritzky)",
        "event": "London, 1851",
        "white": "Adolf Anderssen",
        "black": "Lionel Kieseritzky",
        "description": "A dazzling King's Gambit where White sacrifices both rooks, a bishop, and the Queen to deliver a poetic checkmate with minor pieces.",
        "pgn": "1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6 7. d3 Nh5 8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6 13. h5 Qg5 14. Qf3 Ng8 15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2 18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2 Na6 21. Nxg7+ Kd8 22. Qf6+ Nxf6 23. Be7# 1-0"
    },
    "fischer": {
        "id": "fischer",
        "title": "Game of the Century (Fischer vs Byrne)",
        "event": "New York, 1956",
        "white": "Donald Byrne",
        "black": "Bobby Fischer (Age 13)",
        "description": "13-year-old Bobby Fischer plays black, unleashes a stunning queen sacrifice on move 17, and weaves a windmill combination for checkmate.",
        "pgn": "1. Nf3 Nf6 2. c4 g6 3. Nc3 Bg7 4. d4 O-O 5. Bf4 d5 6. Qb3 dxc4 7. Qxc4 c6 8. e4 Nbd7 9. Rd1 Nb6 10. Qc5 Bg4 11. Bg5 Na4 12. Qa3 Nxc3 13. bxc3 Nxe4 14. Bxe7 Qb6 15. Bc4 Nxc3 16. Bc5 Rfe8+ 17. Kf1 Be6 18. Bxb6 Bxc4+ 19. Kg1 Ne2+ 20. Kf1 Nxd4+ 21. Kg1 Ne2+ 22. Kf1 Nc3+ 23. Kg1 axb6 24. Qb4 Ra4 25. Qxb6 Nxd1 26. h3 Rxa2 27. Kh2 Nxf2 28. Re1 Rxe1 29. Qd8+ Bf8 30. Nxe1 Bd5 31. Nf3 Ne4 32. Qb8 b5 33. h4 h5 34. Ne5 Kg7 35. Kg1 Bc5+ 36. Kf1 Ng3+ 37. Ke1 Bb4+ 38. Kd1 Bb3+ 39. Kc1 Ne2+ 40. Kb1 Nc3+ 41. Kc1 Rc2# 0-1"
    }
}

class ChessModel:
    @staticmethod
    def create_game(user_id, title="GoChess Smart Session", game_mode="ai", ai_level=2, board_theme="obsidian"):
        sql_mysql = """
            INSERT INTO chess_games (user_id, title, game_mode, ai_level, board_theme, fen, pgn, moves_count, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        sql_sqlite = """
            INSERT INTO chess_games (user_id, title, game_mode, ai_level, board_theme, fen, pgn, moves_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        initial_fen = chess.STARTING_FEN
        initial_pgn = ""
        params = (user_id, title, game_mode, ai_level, board_theme, initial_fen, initial_pgn, 0, 'active')
        return execute_insert(sql_mysql, sql_sqlite, params)

    @staticmethod
    def get_game(game_id):
        return query_one(
            "SELECT * FROM chess_games WHERE id = %s",
            "SELECT * FROM chess_games WHERE id = ?",
            (game_id,)
        )

    @staticmethod
    def get_user_games(user_id, limit=10):
        return query_all(
            "SELECT * FROM chess_games WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            "SELECT * FROM chess_games WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )

    @staticmethod
    def update_game_state(game_id, fen, pgn, moves_count, status='active', winner=None):
        sql_mysql = """
            UPDATE chess_games
            SET fen = %s, pgn = %s, moves_count = %s, status = %s, winner = %s
            WHERE id = %s
        """
        sql_sqlite = """
            UPDATE chess_games
            SET fen = ?, pgn = ?, moves_count = ?, status = ?, winner = ?
            WHERE id = ?
        """
        params = (fen, pgn, moves_count, status, winner, game_id)
        return execute_update(sql_mysql, sql_sqlite, params)

    @staticmethod
    def evaluate_board(board):
        """
        Heuristic evaluation from White's perspective (positive means White is better).
        Includes Material + Positional Piece Tables + Mobility + King Safety.
        """
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves():
            return 0

        score = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if not piece:
                continue

            ptype = piece.piece_type
            color = piece.color
            
            # Base material
            val = PIECE_VALUES.get(ptype, 0)
            
            # Positional score from piece-square tables
            pst_val = 0
            # From white's perspective, square index 0 is a1, 63 is h8
            sq_idx = sq if color == chess.WHITE else chess.square_mirror(sq)
            
            if ptype == chess.PAWN:
                pst_val = PAWN_TABLE[63 - sq_idx]
            elif ptype == chess.KNIGHT:
                pst_val = KNIGHT_TABLE[63 - sq_idx]
            elif ptype == chess.BISHOP:
                pst_val = BISHOP_TABLE[63 - sq_idx]
            elif ptype == chess.ROOK:
                pst_val = ROOK_TABLE[63 - sq_idx]
            elif ptype == chess.QUEEN:
                pst_val = QUEEN_TABLE[63 - sq_idx]
            elif ptype == chess.KING:
                pst_val = KING_MID_TABLE[63 - sq_idx]

            total_piece_score = val + pst_val
            if color == chess.WHITE:
                score += total_piece_score
            else:
                score -= total_piece_score

        # Add small mobility bonus
        white_mobility = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0
        board.turn = not board.turn
        black_mobility = len(list(board.legal_moves)) if board.turn == chess.BLACK else 0
        board.turn = not board.turn
        score += (white_mobility - black_mobility) * 5

        return score

    @classmethod
    def minimax(cls, board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.is_game_over():
            return cls.evaluate_board(board), None

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return cls.evaluate_board(board), None

        # Sort moves to improve alpha-beta pruning (captures first)
        legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

        best_move = legal_moves[0]

        if maximizing_player:
            max_eval = -float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score, _ = cls.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score, _ = cls.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    @classmethod
    def get_ai_move(cls, board, level=2):
        """
        Calculate AI move according to GoChess level:
        Level 1: Novice (depth 1)
        Level 2: Club (depth 2)
        Level 3: Master (depth 3)
        Level 4: Grandmaster (depth 4)
        """
        depth_map = {1: 1, 2: 2, 3: 3, 4: 4}
        depth = depth_map.get(level, 2)
        maximizing = (board.turn == chess.WHITE)
        score, move = cls.minimax(board, depth, -float('inf'), float('inf'), maximizing)
        return move, score

    @classmethod
    def get_coach_hints(cls, board):
        """
        Generate GoChess RGB LED Coaching hints:
        - best_move: {from: sq, to: sq, uci: str, san: str}
        - legal_moves: mapping of square -> [valid targets]
        - check_square: square of king if in check
        - hanging_pieces: pieces undefended or under attack
        - eval_score: advantage in centipawns or mate
        """
        if board.is_game_over():
            return {"status": "game_over"}

        # Find best move for current turn
        maximizing = (board.turn == chess.WHITE)
        score, best_move = cls.minimax(board, 2, -float('inf'), float('inf'), maximizing)
        
        best_move_dict = None
        if best_move:
            best_move_dict = {
                "uci": best_move.uci(),
                "san": board.san(best_move),
                "from": chess.square_name(best_move.from_square),
                "to": chess.square_name(best_move.to_square),
                "is_capture": board.is_capture(best_move)
            }

        # Map all legal moves for LED projection
        moves_map = {}
        for m in board.legal_moves:
            from_sq = chess.square_name(m.from_square)
            to_sq = chess.square_name(m.to_square)
            if from_sq not in moves_map:
                moves_map[from_sq] = []
            moves_map[from_sq].append(to_sq)

        # Check square
        check_sq = None
        if board.is_check():
            king_sq = board.king(board.turn)
            if king_sq is not None:
                check_sq = chess.square_name(king_sq)

        return {
            "best_move": best_move_dict,
            "moves_map": moves_map,
            "check_square": check_sq,
            "eval_score": score,
            "eval_advantage_white": score / 100.0,
            "turn": "white" if board.turn == chess.WHITE else "black"
        }

    @staticmethod
    def get_famous_game_playback(game_id):
        game_info = FAMOUS_GAMES.get(game_id)
        if not game_info:
            return None
        
        pgn_io = io.StringIO(game_info["pgn"])
        game = chess.pgn.read_game(pgn_io)
        board = game.board()
        
        steps = []
        # Initial step
        steps.append({
            "step": 0,
            "fen": board.fen(),
            "move_san": "Start",
            "from_sq": None,
            "to_sq": None,
            "comment": "Initial starting position of the historic encounter."
        })

        step_idx = 1
        for move in game.mainline_moves():
            from_sq = chess.square_name(move.from_square)
            to_sq = chess.square_name(move.to_square)
            san = board.san(move)
            board.push(move)
            steps.append({
                "step": step_idx,
                "fen": board.fen(),
                "move_san": san,
                "from_sq": from_sq,
                "to_sq": to_sq,
                "captured": board.is_capture(move)
            })
            step_idx += 1

        return {
            "info": game_info,
            "steps": steps,
            "total_steps": len(steps)
        }

    @staticmethod
    def create_clan_challenge(game_id, group_id, user_id, challenge_note):
        sql_mysql = """
            INSERT INTO chess_clan_challenges (game_id, group_id, user_id, challenge_note, status)
            VALUES (%s, %s, %s, %s, 'open')
        """
        sql_sqlite = """
            INSERT INTO chess_clan_challenges (game_id, group_id, user_id, challenge_note, status)
            VALUES (?, ?, ?, ?, 'open')
        """
        return execute_insert(sql_mysql, sql_sqlite, (game_id, group_id, user_id, challenge_note))
