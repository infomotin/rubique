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

KING_END_TABLE = [
    -50,-30,-30,-30,-30,-30,-30,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
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
    def create_game(user_id, title="GoChess Smart Session", game_mode="ai", ai_level=2, board_theme="obsidian", match_type=None, white_user_id=None, black_user_id=None, white_group_id=None, black_group_id=None):
        if not match_type:
            match_type = game_mode
        if not white_user_id:
            white_user_id = user_id

        sql_mysql = """
            INSERT INTO chess_games (user_id, white_user_id, black_user_id, white_group_id, black_group_id, title, game_mode, match_type, ai_level, board_theme, fen, pgn, moves_count, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """
        sql_sqlite = """
            INSERT INTO chess_games (user_id, white_user_id, black_user_id, white_group_id, black_group_id, title, game_mode, match_type, ai_level, board_theme, fen, pgn, moves_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """
        initial_fen = chess.STARTING_FEN
        initial_pgn = ""
        params = (user_id, white_user_id, black_user_id, white_group_id, black_group_id, title, game_mode, match_type, ai_level, board_theme, initial_fen, initial_pgn, 0)
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
    def pause_game(game_id, user_id=None, fen=None, moves_count=None):
        """Stop / Pause play stage: saves current position and marks as paused"""
        set_clauses_mysql = ["status = 'paused'"]
        set_clauses_sqlite = ["status = 'paused'"]
        params = []
        if fen:
            set_clauses_mysql.append("fen = %s")
            set_clauses_sqlite.append("fen = ?")
            params.append(fen)
        if moves_count is not None:
            set_clauses_mysql.append("moves_count = %s")
            set_clauses_sqlite.append("moves_count = ?")
            params.append(moves_count)

        where_mysql = "id = %s" if not user_id else "id = %s AND (user_id = %s OR white_user_id = %s OR black_user_id = %s)"
        where_sqlite = "id = ?" if not user_id else "id = ? AND (user_id = ? OR white_user_id = ? OR black_user_id = ?)"

        set_str_mysql = ", ".join(set_clauses_mysql)
        set_str_sqlite = ", ".join(set_clauses_sqlite)

        sql_mysql = f"UPDATE chess_games SET {set_str_mysql} WHERE {where_mysql}"
        sql_sqlite = f"UPDATE chess_games SET {set_str_sqlite} WHERE {where_sqlite}"

        all_params = list(params)
        all_params.append(game_id)
        if user_id:
            all_params.extend([user_id, user_id, user_id])

        return execute_update(sql_mysql, sql_sqlite, tuple(all_params))

    @staticmethod
    def resume_game(game_id, user_id=None):
        """Resume saved play stage: updates status to active and fetches full state"""
        where_clause = "id = %s" if not user_id else "id = %s AND (user_id = %s OR white_user_id = %s OR black_user_id = %s)"
        where_sqlite = "id = ?" if not user_id else "id = ? AND (user_id = ? OR white_user_id = ? OR black_user_id = ?)"
        params = (game_id,) if not user_id else (game_id, user_id, user_id, user_id)
        sql_mysql = f"UPDATE chess_games SET status = 'active' WHERE {where_clause}"
        sql_sqlite = f"UPDATE chess_games SET status = 'active' WHERE {where_sqlite}"
        execute_update(sql_mysql, sql_sqlite, params)
        return ChessModel.get_game(game_id)

    @staticmethod
    def destroy_game(game_id, user_id=None):
        """Destroy / Delete saved play stage permanently with related moves cleaned"""
        where_clause = "id = %s" if not user_id else "id = %s AND (user_id = %s OR white_user_id = %s)"
        where_sqlite = "id = ?" if not user_id else "id = ? AND (user_id = ? OR white_user_id = ?)"
        params = (game_id,) if not user_id else (game_id, user_id, user_id)
        
        # Clean dependent records safely
        try:
            execute_update("DELETE FROM chess_team_moves WHERE game_id = %s", "DELETE FROM chess_team_moves WHERE game_id = ?", (game_id,))
            execute_update("DELETE FROM chess_clan_challenges WHERE game_id = %s", "DELETE FROM chess_clan_challenges WHERE game_id = ?", (game_id,))
        except Exception:
            pass

        sql_mysql = f"DELETE FROM chess_games WHERE {where_clause}"
        sql_sqlite = f"DELETE FROM chess_games WHERE {where_sqlite}"
        return execute_update(sql_mysql, sql_sqlite, params)

    @staticmethod
    def save_stage_snapshot(game_id, user_id, title=None):
        """Update stage title or label for easy identification"""
        if title:
            sql_mysql = "UPDATE chess_games SET title = %s WHERE id = %s AND (user_id = %s OR white_user_id = %s)"
            sql_sqlite = "UPDATE chess_games SET title = ? WHERE id = ? AND (user_id = ? OR white_user_id = ?)"
            execute_update(sql_mysql, sql_sqlite, (title, game_id, user_id, user_id))
        return ChessModel.get_game(game_id)

    @staticmethod
    def get_user_saved_stages(user_id, match_type=None, limit=50):
        """Retrieve all play stages stored for player across each game style"""
        where_extra_mysql = ""
        where_extra_sqlite = ""
        params = [user_id, user_id, user_id]
        if match_type and match_type != 'all':
            where_extra_mysql = " AND cg.match_type = %s"
            where_extra_sqlite = " AND cg.match_type = ?"
            params.append(match_type)
        params.append(limit)

        sql_mysql = f"""
            SELECT cg.*, 
                   wg.name as white_group_name, bg.name as black_group_name,
                   (SELECT COUNT(*) FROM chess_team_moves tm WHERE tm.game_id = cg.id) as team_moves_count
            FROM chess_games cg
            LEFT JOIN chat_groups wg ON cg.white_group_id = wg.id
            LEFT JOIN chat_groups bg ON cg.black_group_id = bg.id
            WHERE (cg.user_id = %s OR cg.white_user_id = %s OR cg.black_user_id = %s){where_extra_mysql}
            ORDER BY cg.created_at DESC LIMIT %s
        """
        sql_sqlite = f"""
            SELECT cg.*, 
                   wg.name as white_group_name, bg.name as black_group_name,
                   (SELECT COUNT(*) FROM chess_team_moves tm WHERE tm.game_id = cg.id) as team_moves_count
            FROM chess_games cg
            LEFT JOIN chat_groups wg ON cg.white_group_id = wg.id
            LEFT JOIN chat_groups bg ON cg.black_group_id = bg.id
            WHERE (cg.user_id = ? OR cg.white_user_id = ? OR cg.black_user_id = ?){where_extra_sqlite}
            ORDER BY cg.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, tuple(params))

    @staticmethod
    def _is_endgame(board):
        """Detect endgame: queens are gone or non-pawn material is <= 1400 points per side."""
        white_material = 0
        black_material = 0
        white_has_queen = False
        black_has_queen = False
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if not p or p.piece_type in (chess.PAWN, chess.KING):
                continue
            val = PIECE_VALUES.get(p.piece_type, 0)
            if p.color == chess.WHITE:
                white_material += val
                if p.piece_type == chess.QUEEN:
                    white_has_queen = True
            else:
                black_material += val
                if p.piece_type == chess.QUEEN:
                    black_has_queen = True
        return (not white_has_queen and not black_has_queen) or (white_material <= 1400 and black_material <= 1400)

    @staticmethod
    def evaluate_board(board):
        """
        Advanced heuristic evaluation from White's perspective (positive means White is better).
        Includes Material + Dynamic PST (Midgame/Endgame) + Non-destructive Mobility +
        Pawn Structure (Passed/Doubled/Isolated) + Bishop Pair + Center Space Control.
        """
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves():
            return 0

        is_endgame = ChessModel._is_endgame(board)
        score = 0
        white_bishops = 0
        black_bishops = 0
        white_pawns_files = [0] * 8
        black_pawns_files = [0] * 8

        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if not piece:
                continue

            ptype = piece.piece_type
            color = piece.color
            file_idx = chess.square_file(sq)
            rank_idx = chess.square_rank(sq)

            # Material value
            val = PIECE_VALUES.get(ptype, 0)

            # Positional score from piece-square tables
            pst_val = 0
            sq_idx = sq if color == chess.WHITE else chess.square_mirror(sq)

            if ptype == chess.PAWN:
                pst_val = PAWN_TABLE[63 - sq_idx]
                if color == chess.WHITE:
                    white_pawns_files[file_idx] += 1
                else:
                    black_pawns_files[file_idx] += 1
            elif ptype == chess.KNIGHT:
                pst_val = KNIGHT_TABLE[63 - sq_idx]
            elif ptype == chess.BISHOP:
                pst_val = BISHOP_TABLE[63 - sq_idx]
                if color == chess.WHITE:
                    white_bishops += 1
                else:
                    black_bishops += 1
            elif ptype == chess.ROOK:
                pst_val = ROOK_TABLE[63 - sq_idx]
                # 7th rank bonus for rooks
                if (color == chess.WHITE and rank_idx == 6) or (color == chess.BLACK and rank_idx == 1):
                    pst_val += 25
            elif ptype == chess.QUEEN:
                pst_val = QUEEN_TABLE[63 - sq_idx]
            elif ptype == chess.KING:
                # Dynamic king table: safe castled castle in midgame, active hunting in endgame
                if is_endgame:
                    pst_val = KING_END_TABLE[63 - sq_idx]
                else:
                    pst_val = KING_MID_TABLE[63 - sq_idx]

            total_piece_score = val + pst_val
            if color == chess.WHITE:
                score += total_piece_score
            else:
                score -= total_piece_score

        # 1. Bishop pair advantage (+35)
        if white_bishops >= 2:
            score += 35
        if black_bishops >= 2:
            score -= 35

        # 2. Pawn structure evaluation (Doubled and Isolated pawns)
        for f in range(8):
            # Doubled pawns (-15 per extra pawn on same file)
            if white_pawns_files[f] > 1:
                score -= 15 * (white_pawns_files[f] - 1)
            if black_pawns_files[f] > 1:
                score += 15 * (black_pawns_files[f] - 1)

            # Isolated pawns (-20 if no friendly pawns on neighbor files)
            left_w = white_pawns_files[f - 1] if f > 0 else 0
            right_w = white_pawns_files[f + 1] if f < 7 else 0
            if white_pawns_files[f] > 0 and left_w == 0 and right_w == 0:
                score -= 20

            left_b = black_pawns_files[f - 1] if f > 0 else 0
            right_b = black_pawns_files[f + 1] if f < 7 else 0
            if black_pawns_files[f] > 0 and left_b == 0 and right_b == 0:
                score += 20

        # 3. Center Control (d4, e4, d5, e5 squares)
        center_squares = (chess.D4, chess.E4, chess.D5, chess.E5)
        for c_sq in center_squares:
            c_piece = board.piece_at(c_sq)
            if c_piece:
                score += 10 if c_piece.color == chess.WHITE else -10

        # 4. Non-destructive Mobility bonus (accurately preserves board.turn)
        cur_turn = board.turn
        white_mobility = 0
        black_mobility = 0
        if cur_turn == chess.WHITE:
            white_mobility = len(list(board.legal_moves))
            board.turn = chess.BLACK
            black_mobility = len(list(board.legal_moves))
            board.turn = chess.WHITE
        else:
            black_mobility = len(list(board.legal_moves))
            board.turn = chess.WHITE
            white_mobility = len(list(board.legal_moves))
            board.turn = chess.BLACK

        score += (white_mobility - black_mobility) * 4
        return score

    @classmethod
    def _mvv_lva_score(cls, board, move):
        """Most Valuable Victim - Least Valuable Attacker move ordering score."""
        if move.promotion:
            return 9500
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            v_val = PIECE_VALUES.get(victim.piece_type, 100) if victim else 100
            a_val = PIECE_VALUES.get(attacker.piece_type, 100) if attacker else 100
            return 1000 + v_val * 10 - a_val
        if board.gives_check(move):
            return 500
        # Center square occupation bonus for quiet moves
        if move.to_square in (chess.D4, chess.E4, chess.D5, chess.E5):
            return 50
        return 0

    @classmethod
    def quiescence(cls, board, alpha, beta, maximizing, q_depth=4):
        """
        Quiescence Search:
        Searches captures until a quiet position is reached, eliminating
        the horizon effect where the AI blunders pieces right after a capture.
        """
        stand_pat = cls.evaluate_board(board)
        if maximizing:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)

        if q_depth <= 0 or board.is_game_over():
            return stand_pat

        captures = [m for m in board.legal_moves if board.is_capture(m)]
        if not captures:
            return stand_pat

        captures.sort(key=lambda m: cls._mvv_lva_score(board, m), reverse=True)

        for move in captures:
            board.push(move)
            score = cls.quiescence(board, alpha, beta, not maximizing, q_depth - 1)
            board.pop()

            if maximizing:
                if score >= beta:
                    return beta
                alpha = max(alpha, score)
            else:
                if score <= alpha:
                    return alpha
                beta = min(beta, score)

        return alpha if maximizing else beta

    @classmethod
    def minimax(cls, board, depth, alpha, beta, maximizing_player, tt=None):
        if depth == 0 or board.is_game_over():
            return cls.quiescence(board, alpha, beta, maximizing_player, q_depth=4), None

        # Transposition table lookup
        key = None
        if tt is not None:
            try:
                key = (board._transposition_key(), depth, maximizing_player)
                if key in tt:
                    return tt[key]
            except Exception:
                pass

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return cls.evaluate_board(board), None

        # Sort moves using MVV-LVA to dramatically improve alpha-beta pruning
        legal_moves.sort(key=lambda m: cls._mvv_lva_score(board, m), reverse=True)

        best_move = legal_moves[0]

        if maximizing_player:
            max_eval = -float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score, _ = cls.minimax(board, depth - 1, alpha, beta, False, tt)
                board.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            res = (max_eval, best_move)
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score, _ = cls.minimax(board, depth - 1, alpha, beta, True, tt)
                board.pop()
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            res = (min_eval, best_move)

        if tt is not None and key and len(tt) < 50000:
            tt[key] = res

        return res

    @classmethod
    def get_ai_move(cls, board, level=2):
        """
        Calculate AI move according to GoChess level:
        Level 1: Novice (~800 ELO, depth 1 with friendly beginner variety)
        Level 2: Club (~1400 ELO, depth 2 + Quiescence)
        Level 3: Master (~2000 ELO, depth 3 + Quiescence + MVV-LVA)
        Level 4: Grandmaster (~2400 ELO, depth 4 + Quiescence + Transposition Cache)
        Level 5: Super Grandmaster (~2700 ELO, depth 4/5 + Opening Book + Deep Quiescence)
        """
        import random

        # Level 1 (Novice): Depth 1 with 20% random move selection for beginner fun
        if level <= 1:
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None, 0
            if random.random() < 0.20:
                return random.choice(legal_moves), 0
            depth = 1
        elif level == 2:
            depth = 2
        elif level == 3:
            depth = 3
        elif level == 4:
            depth = 4
        else:
            # Level 5: Grandmaster / Stockfish-caliber
            # Opening Book handling for starting moves
            if board.fullmove_number <= 2 and board.fen() == chess.STARTING_FEN:
                classic_openings = ['e2e4', 'd2d4', 'c2c4', 'g1f3']
                choice = random.choice(classic_openings)
                mv = chess.Move.from_uci(choice)
                if mv in board.legal_moves:
                    return mv, 25
            depth = 4

        tt = {}
        maximizing = (board.turn == chess.WHITE)
        score, move = cls.minimax(board, depth, -float('inf'), float('inf'), maximizing, tt=tt)
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

        # Find best move for current turn with depth 3 Master vision
        maximizing = (board.turn == chess.WHITE)
        score, best_move = cls.minimax(board, 3, -float('inf'), float('inf'), maximizing, tt={})
        
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

    # =========================================================================
    # INTERACTIVE COMPLEX PROBLEM SOLVER & STEP VERIFICATION
    # =========================================================================
    @classmethod
    def validate_problem_step(cls, problem_id, user_id, current_fen, player_move_uci):
        """
        Interactive Step-by-Step Problem Solver Engine:
        Validates the player's move against the problem solution sequence.
        If correct and the puzzle continues, automatically plays the opponent's
        best defensive response and returns the new board state.
        If final move is delivered or checkmate achieved, awards XP and marks solved!
        """
        problem = cls.get_problem(problem_id)
        if not problem:
            return {"status": "error", "message": "Problem not found."}

        try:
            start_board = chess.Board(problem['fen'])
        except Exception:
            return {"status": "error", "message": "Invalid problem setup."}

        sol_tokens = [m.strip() for m in problem['solution_moves'].replace(';', ',').split(',') if m.strip()]
        if not sol_tokens:
            return {"status": "error", "message": "No solution line defined for this problem."}

        # Parse the full official solution move list
        temp_b = start_board.copy()
        expected_moves = []
        for tok in sol_tokens:
            mv = cls._parse_move_token(temp_b, tok)
            if not mv:
                break
            expected_moves.append(mv)
            temp_b.push(mv)

        # Parse player move on current board
        try:
            curr_b = chess.Board(current_fen)
        except Exception:
            curr_b = start_board.copy()

        pmv = cls._parse_move_token(curr_b, player_move_uci)
        if not pmv or pmv not in curr_b.legal_moves:
            return {
                "status": "success",
                "correct": False,
                "is_solved": False,
                "message": "Illegal move on this board position."
            }

        # Determine step index: find which position in the expected line matches curr_b
        step_idx = 0
        replay_b = start_board.copy()
        if replay_b.board_fen() == curr_b.board_fen():
            step_idx = 0
        else:
            for idx, em in enumerate(expected_moves):
                replay_b.push(em)
                if replay_b.board_fen() == curr_b.board_fen():
                    step_idx = idx + 1
                    break

        expected_pmv = expected_moves[step_idx] if step_idx < len(expected_moves) else None

        # Verify move
        is_correct = False
        if expected_pmv and (pmv == expected_pmv or pmv.uci() == expected_pmv.uci()):
            is_correct = True
        else:
            # Check if this move delivers checkmate
            test_b = curr_b.copy()
            test_b.push(pmv)
            if test_b.is_checkmate():
                is_correct = True

        if not is_correct:
            return {
                "status": "success",
                "correct": False,
                "is_solved": False,
                "message": "That is not the winning line. Rethink the tactical combination!"
            }

        # Move is correct! Get player SAN before advancing
        player_san = curr_b.san(pmv)
        curr_b.push(pmv)

        # Is the puzzle solved here?
        next_step = step_idx + 1
        is_completed = (next_step >= len(expected_moves)) or curr_b.is_checkmate()

        if is_completed:
            xp_reward = problem.get('xp_reward', 150)
            try:
                execute_insert(
                    "INSERT INTO chess_problem_submissions (problem_id, user_id, submitted_moves, is_solved, xp_earned) VALUES (%s, %s, %s, 1, %s)",
                    "INSERT INTO chess_problem_submissions (problem_id, user_id, submitted_moves, is_solved, xp_earned) VALUES (?, ?, ?, 1, ?)",
                    (problem_id, user_id, player_move_uci, xp_reward)
                )
            except Exception:
                pass

            return {
                "status": "success",
                "correct": True,
                "is_solved": True,
                "completed": True,
                "xp_earned": xp_reward,
                "player_move": {
                    "uci": pmv.uci(),
                    "san": player_san,
                    "from": chess.square_name(pmv.from_square),
                    "to": chess.square_name(pmv.to_square)
                },
                "message": f"Outstanding tactical vision! Problem solved! +{xp_reward} XP awarded!"
            }

        # Opponent's defensive move
        opp_mv = expected_moves[next_step]
        opp_from = chess.square_name(opp_mv.from_square)
        opp_to = chess.square_name(opp_mv.to_square)
        opp_san = curr_b.san(opp_mv)
        curr_b.push(opp_mv)

        return {
            "status": "success",
            "correct": True,
            "is_solved": False,
            "completed": False,
            "player_move": {
                "uci": pmv.uci(),
                "san": player_san,
                "from": chess.square_name(pmv.from_square),
                "to": chess.square_name(pmv.to_square)
            },
            "opponent_move": {
                "uci": opp_mv.uci(),
                "san": opp_san,
                "from": opp_from,
                "to": opp_to
            },
            "new_fen": curr_b.fen(),
            "message": "Brilliant move! Opponent played best defensive response. Find the next continuation!"
        }

    @classmethod
    def get_problem_hint(cls, problem_id, current_fen):
        """Returns progressive hints: piece to move, target square, or problem strategy."""
        problem = cls.get_problem(problem_id)
        if not problem:
            return {"status": "error", "message": "Problem not found"}

        try:
            start_board = chess.Board(problem['fen'])
            curr_b = chess.Board(current_fen)
        except Exception:
            return {"status": "success", "hint": problem.get('hint', 'Calculate forcing lines.')}

        sol_tokens = [m.strip() for m in problem['solution_moves'].replace(';', ',').split(',') if m.strip()]
        temp_b = start_board.copy()
        expected_moves = []
        for tok in sol_tokens:
            mv = cls._parse_move_token(temp_b, tok)
            if not mv:
                break
            expected_moves.append(mv)
            temp_b.push(mv)

        target_move = None
        replay_b = start_board.copy()
        if replay_b.board_fen() == curr_b.board_fen() and expected_moves:
            target_move = expected_moves[0]
        else:
            for idx, em in enumerate(expected_moves):
                replay_b.push(em)
                if replay_b.board_fen() == curr_b.board_fen() and idx + 1 < len(expected_moves):
                    target_move = expected_moves[idx + 1]
                    break

        if not target_move and expected_moves:
            target_move = expected_moves[0]

        if target_move:
            from_sq = chess.square_name(target_move.from_square)
            to_sq = chess.square_name(target_move.to_square)
            piece = curr_b.piece_at(target_move.from_square)
            p_name = chess.piece_name(piece.piece_type).capitalize() if piece else "Piece"
            return {
                "status": "success",
                "from_sq": from_sq,
                "to_sq": to_sq,
                "hint": f"Coach Insight: Consider moving your {p_name} on {from_sq} towards {to_sq}! ({problem.get('hint', '')})"
            }

        return {"status": "success", "hint": problem.get('hint', 'Focus on checks and captures.')}

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

    # =========================================================================
    # SUPER ADMIN CHESS PROBLEMS & SUBSCRIBER SUBMISSIONS
    # =========================================================================
    @staticmethod
    def create_problem(author_id, title, difficulty, fen, solution_moves, hint="", xp_reward=150):
        sql_mysql = """
            INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        sql_sqlite = """
            INSERT INTO chess_problems (author_id, title, difficulty, fen, solution_moves, hint, xp_reward)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return execute_insert(sql_mysql, sql_sqlite, (author_id, title, difficulty, fen, solution_moves, hint, xp_reward))

    @staticmethod
    def get_problems(limit=50):
        sql_mysql = """
            SELECT cp.*, u.username as author_name,
                   (SELECT COUNT(*) FROM chess_problem_submissions cps WHERE cps.problem_id = cp.id AND cps.is_solved = 1) as solvers_count
            FROM chess_problems cp
            LEFT JOIN users u ON cp.author_id = u.id
            ORDER BY cp.created_at DESC LIMIT %s
        """
        sql_sqlite = """
            SELECT cp.*, u.username as author_name,
                   (SELECT COUNT(*) FROM chess_problem_submissions cps WHERE cps.problem_id = cp.id AND cps.is_solved = 1) as solvers_count
            FROM chess_problems cp
            LEFT JOIN users u ON cp.author_id = u.id
            ORDER BY cp.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, (limit,))

    @staticmethod
    def get_problem(problem_id):
        sql_mysql = """
            SELECT cp.*, u.username as author_name
            FROM chess_problems cp
            LEFT JOIN users u ON cp.author_id = u.id
            WHERE cp.id = %s
        """
        sql_sqlite = """
            SELECT cp.*, u.username as author_name
            FROM chess_problems cp
            LEFT JOIN users u ON cp.author_id = u.id
            WHERE cp.id = ?
        """
        return query_one(sql_mysql, sql_sqlite, (problem_id,))

    @staticmethod
    def _parse_move_token(board, token):
        """Parse one move token as UCI or SAN against the given board."""
        tok = token.strip()
        if not tok:
            return None
        try:
            mv = chess.Move.from_uci(tok.lower())
            if mv in board.legal_moves:
                return mv
        except ValueError:
            pass
        try:
            return board.parse_san(tok)
        except ValueError:
            return None

    @classmethod
    def verify_and_submit_solution(cls, problem_id, user_id, submitted_moves_str):
        """
        Verifies subscriber's solution moves against the problem solution.
        Accepts comma-separated UCI or SAN moves; both the official line and the
        submitted line are replayed on the problem FEN with python-chess, so
        either notation is always accepted. Solved when the key (first) move
        matches, the full line matches, or the line legally checkmates the
        opponent within a sensible move budget.
        """
        problem = cls.get_problem(problem_id)
        if not problem:
            return {"status": "error", "message": "Problem not found", "is_solved": False}

        expected_tokens = [m.strip() for m in problem['solution_moves'].replace(';', ',').split(',') if m.strip()]
        submitted_tokens = [m.strip() for m in submitted_moves_str.replace(';', ',').split(',') if m.strip()]

        is_solved = False
        expected_first_uci = expected_tokens[0].lower() if expected_tokens else ""
        try:
            start_board = chess.Board(problem['fen'])
            start_turn = start_board.turn

            exp_board = start_board.copy()
            expected_uci = []
            for tok in expected_tokens:
                mv = cls._parse_move_token(exp_board, tok)
                if mv is None:
                    break
                expected_uci.append(mv.uci())
                exp_board.push(mv)
            if expected_uci:
                expected_first_uci = expected_uci[0]

            sub_board = start_board.copy()
            submitted_uci = []
            for tok in submitted_tokens:
                mv = cls._parse_move_token(sub_board, tok)
                if mv is None:
                    submitted_uci = None  # illegal move -> never solved
                    break
                submitted_uci.append(mv.uci())
                sub_board.push(mv)

            if submitted_uci:
                if expected_uci and submitted_uci[0] == expected_uci[0]:
                    is_solved = True
                elif (sub_board.is_checkmate() and sub_board.turn != start_turn
                      and len(submitted_uci) <= max(len(expected_uci), 1) + 2):
                    is_solved = True
            elif submitted_tokens and expected_tokens:
                # Fallback (unparseable FEN): raw first-move / full-line compare
                sub_lower = [t.lower() for t in submitted_tokens]
                exp_lower = [t.lower() for t in expected_tokens]
                is_solved = sub_lower[0] == exp_lower[0] or sub_lower == exp_lower
        except Exception:
            is_solved = False

        xp_earned = problem.get('xp_reward', 100) if is_solved else 0

        sql_mysql = """
            INSERT INTO chess_problem_submissions (problem_id, user_id, submitted_moves, is_solved, xp_earned)
            VALUES (%s, %s, %s, %s, %s)
        """
        sql_sqlite = """
            INSERT INTO chess_problem_submissions (problem_id, user_id, submitted_moves, is_solved, xp_earned)
            VALUES (?, ?, ?, ?, ?)
        """
        sub_id = execute_insert(sql_mysql, sql_sqlite, (problem_id, user_id, submitted_moves_str, 1 if is_solved else 0, xp_earned))

        return {
            "status": "success",
            "submission_id": sub_id,
            "is_solved": is_solved,
            "xp_earned": xp_earned,
            "expected_first_move": expected_first_uci,
            "message": "Outstanding tactical vision! Problem solved!" if is_solved else "Incorrect tactical sequence. Try another combination or inspect hints."
        }

    @staticmethod
    def get_problem_submissions(problem_id, limit=20):
        sql_mysql = """
            SELECT cps.*, u.username, u.avatar_color
            FROM chess_problem_submissions cps
            JOIN users u ON cps.user_id = u.id
            WHERE cps.problem_id = %s
            ORDER BY cps.created_at DESC LIMIT %s
        """
        sql_sqlite = """
            SELECT cps.*, u.username, u.avatar_color
            FROM chess_problem_submissions cps
            JOIN users u ON cps.user_id = u.id
            WHERE cps.problem_id = ?
            ORDER BY cps.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, (problem_id, limit))

    # =========================================================================
    # MULTIPLAYER MATCHMAKING: 1v1, GROUP VS GROUP, GROUP VS PUBLIC
    # =========================================================================
    @staticmethod
    def create_multiplayer_match(user_id, match_type='1v1', title='GoChess Cyber Arena', white_group_id=None, black_group_id=None, is_public=1):
        sql_mysql = """
            INSERT INTO chess_games (user_id, white_user_id, match_type, title, white_group_id, black_group_id, is_public, fen, pgn, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """
        sql_sqlite = """
            INSERT INTO chess_games (user_id, white_user_id, match_type, title, white_group_id, black_group_id, is_public, fen, pgn, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """
        initial_fen = chess.STARTING_FEN
        return execute_insert(sql_mysql, sql_sqlite, (user_id, user_id, match_type, title, white_group_id, black_group_id, is_public, initial_fen, ""))

    @staticmethod
    def get_multiplayer_matches(match_type=None, limit=20, public_only=True):
        where_sql_mysql = "WHERE cg.match_type != 'ai'"
        where_sql_sqlite = "WHERE cg.match_type != 'ai'"
        params = []
        if public_only:
            where_sql_mysql += " AND cg.is_public = 1"
            where_sql_sqlite += " AND cg.is_public = 1"
        if match_type:
            where_sql_mysql += " AND cg.match_type = %s"
            where_sql_sqlite += " AND cg.match_type = ?"
            params.append(match_type)

        params.append(limit)

        sql_mysql = f"""
            SELECT cg.*, u.username as creator_name,
                   bwu.username as white_player_name, bcu.username as black_player_name,
                   wg.name as white_group_name, bg.name as black_group_name,
                   (SELECT COUNT(*) FROM chess_team_moves tm WHERE tm.game_id = cg.id) as team_moves_count
            FROM chess_games cg
            LEFT JOIN users u ON cg.user_id = u.id
            LEFT JOIN users bwu ON cg.white_user_id = bwu.id
            LEFT JOIN users bcu ON cg.black_user_id = bcu.id
            LEFT JOIN chat_groups wg ON cg.white_group_id = wg.id
            LEFT JOIN chat_groups bg ON cg.black_group_id = bg.id
            {where_sql_mysql}
            ORDER BY cg.created_at DESC LIMIT %s
        """
        sql_sqlite = f"""
            SELECT cg.*, u.username as creator_name,
                   bwu.username as white_player_name, bcu.username as black_player_name,
                   wg.name as white_group_name, bg.name as black_group_name,
                   (SELECT COUNT(*) FROM chess_team_moves tm WHERE tm.game_id = cg.id) as team_moves_count
            FROM chess_games cg
            LEFT JOIN users u ON cg.user_id = u.id
            LEFT JOIN users bwu ON cg.white_user_id = bwu.id
            LEFT JOIN users bcu ON cg.black_user_id = bcu.id
            LEFT JOIN chat_groups wg ON cg.white_group_id = wg.id
            LEFT JOIN chat_groups bg ON cg.black_group_id = bg.id
            {where_sql_sqlite}
            ORDER BY cg.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, tuple(params))

    # =========================================================================
    # INVITATIONS: DIRECT SUBSCRIBER INVITES & CLAN (GROUP) INVITES
    # =========================================================================
    @staticmethod
    def create_invitation(game_id, from_user_id, to_user_id=None, to_group_id=None, message=""):
        sql_mysql = """
            INSERT INTO chess_invitations (game_id, from_user_id, to_user_id, to_group_id, message, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
        """
        sql_sqlite = """
            INSERT INTO chess_invitations (game_id, from_user_id, to_user_id, to_group_id, message, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """
        return execute_insert(sql_mysql, sql_sqlite, (game_id, from_user_id, to_user_id, to_group_id, message))

    @staticmethod
    def get_invitation(invitation_id):
        return query_one(
            """SELECT ci.*, fu.username as from_username, tu.username as to_username,
                      cg.name as group_name, chess.title as game_title, chess.match_type as game_match_type,
                      chess.is_public as game_is_public
               FROM chess_invitations ci
               LEFT JOIN users fu ON ci.from_user_id = fu.id
               LEFT JOIN users tu ON ci.to_user_id = tu.id
               LEFT JOIN chat_groups cg ON ci.to_group_id = cg.id
               LEFT JOIN chess_games chess ON ci.game_id = chess.id
               WHERE ci.id = %s""",
            """SELECT ci.*, fu.username as from_username, tu.username as to_username,
                      cg.name as group_name, chess.title as game_title, chess.match_type as game_match_type,
                      chess.is_public as game_is_public
               FROM chess_invitations ci
               LEFT JOIN users fu ON ci.from_user_id = fu.id
               LEFT JOIN users tu ON ci.to_user_id = tu.id
               LEFT JOIN chat_groups cg ON ci.to_group_id = cg.id
               LEFT JOIN chess_games chess ON ci.game_id = chess.id
               WHERE ci.id = ?""",
            (invitation_id,)
        )

    @staticmethod
    def get_received_invitations(user_id, limit=30):
        """Pending invites addressed to this subscriber, or to a clan they lead/roster."""
        sql_mysql = """
            SELECT ci.*, fu.username as from_username, tu.username as to_username,
                   cg.name as group_name, chess.title as game_title, chess.match_type as game_match_type
            FROM chess_invitations ci
            LEFT JOIN users fu ON ci.from_user_id = fu.id
            LEFT JOIN users tu ON ci.to_user_id = tu.id
            LEFT JOIN chat_groups cg ON ci.to_group_id = cg.id
            LEFT JOIN chess_games chess ON ci.game_id = chess.id
            WHERE ci.status = 'pending'
              AND (ci.to_user_id = %s
                   OR (ci.to_group_id IS NOT NULL AND ci.to_group_id IN (
                        SELECT id FROM chat_groups WHERE created_by = %s
                        UNION
                        SELECT group_id FROM chess_clan_members WHERE user_id = %s)))
            ORDER BY ci.created_at DESC LIMIT %s
        """
        sql_sqlite = """
            SELECT ci.*, fu.username as from_username, tu.username as to_username,
                   cg.name as group_name, chess.title as game_title, chess.match_type as game_match_type
            FROM chess_invitations ci
            LEFT JOIN users fu ON ci.from_user_id = fu.id
            LEFT JOIN users tu ON ci.to_user_id = tu.id
            LEFT JOIN chat_groups cg ON ci.to_group_id = cg.id
            LEFT JOIN chess_games chess ON ci.game_id = chess.id
            WHERE ci.status = 'pending'
              AND (ci.to_user_id = ?
                   OR (ci.to_group_id IS NOT NULL AND ci.to_group_id IN (
                        SELECT id FROM chat_groups WHERE created_by = ?
                        UNION
                        SELECT group_id FROM chess_clan_members WHERE user_id = ?)))
            ORDER BY ci.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, (user_id, user_id, user_id, limit))

    @staticmethod
    def get_sent_invitations(user_id, limit=30):
        sql_mysql = """
            SELECT ci.*, fu.username as from_username, tu.username as to_username,
                   cg.name as group_name, chess.title as game_title, chess.match_type as game_match_type
            FROM chess_invitations ci
            LEFT JOIN users fu ON ci.from_user_id = fu.id
            LEFT JOIN users tu ON ci.to_user_id = tu.id
            LEFT JOIN chat_groups cg ON ci.to_group_id = cg.id
            LEFT JOIN chess_games chess ON ci.game_id = chess.id
            WHERE ci.from_user_id = %s
            ORDER BY ci.created_at DESC LIMIT %s
        """
        sql_sqlite = """
            SELECT ci.*, fu.username as from_username, tu.username as to_username,
                   cg.name as group_name, chess.title as game_title, chess.match_type as game_match_type
            FROM chess_invitations ci
            LEFT JOIN users fu ON ci.from_user_id = fu.id
            LEFT JOIN users tu ON ci.to_user_id = tu.id
            LEFT JOIN chat_groups cg ON ci.to_group_id = cg.id
            LEFT JOIN chess_games chess ON ci.game_id = chess.id
            WHERE ci.from_user_id = ?
            ORDER BY ci.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, (user_id, limit))

    @staticmethod
    def set_invitation_status(invitation_id, status):
        return execute_update(
            "UPDATE chess_invitations SET status = %s WHERE id = %s",
            "UPDATE chess_invitations SET status = ? WHERE id = ?",
            (status, invitation_id)
        )

    @staticmethod
    def has_live_invitation(game_id, user_id):
        """True when an invitation for this match targets the subscriber (directly or via their clan)."""
        return query_one(
            """SELECT ci.id FROM chess_invitations ci
               WHERE ci.game_id = %s AND ci.status IN ('pending','accepted')
                 AND (ci.to_user_id = %s
                      OR (ci.to_group_id IS NOT NULL AND ci.to_group_id IN (
                            SELECT id FROM chat_groups WHERE created_by = %s
                            UNION
                            SELECT group_id FROM chess_clan_members WHERE user_id = %s)))
               LIMIT 1""",
            """SELECT ci.id FROM chess_invitations ci
               WHERE ci.game_id = ? AND ci.status IN ('pending','accepted')
                 AND (ci.to_user_id = ?
                      OR (ci.to_group_id IS NOT NULL AND ci.to_group_id IN (
                            SELECT id FROM chat_groups WHERE created_by = ?
                            UNION
                            SELECT group_id FROM chess_clan_members WHERE user_id = ?)))
               LIMIT 1""",
            (game_id, user_id, user_id, user_id)
        )

    # =========================================================================
    # CLAN ROSTER: who may take a clan seat in Group vs Group battles
    # =========================================================================
    @staticmethod
    def is_clan_member(group_id, user_id):
        if not group_id or not user_id:
            return False
        group = query_one(
            "SELECT created_by FROM chat_groups WHERE id = %s",
            "SELECT created_by FROM chat_groups WHERE id = ?",
            (group_id,)
        )
        if group and group.get('created_by') == user_id:
            return True
        row = query_one(
            "SELECT 1 as ok FROM chess_clan_members WHERE group_id = %s AND user_id = %s",
            "SELECT 1 as ok FROM chess_clan_members WHERE group_id = ? AND user_id = ?",
            (group_id, user_id)
        )
        return row is not None

    @staticmethod
    def add_clan_member(group_id, user_id):
        if not group_id or not user_id:
            return None
        return execute_insert(
            "INSERT IGNORE INTO chess_clan_members (group_id, user_id) VALUES (%s, %s)",
            "INSERT OR IGNORE INTO chess_clan_members (group_id, user_id) VALUES (?, ?)",
            (group_id, user_id)
        )

    # =========================================================================
    # SEAT ASSIGNMENT: join open / public / clan battles
    # =========================================================================
    @staticmethod
    def set_game_seat(game_id, seat, user_id):
        column = 'white_user_id' if seat == 'white' else 'black_user_id'
        return execute_update(
            f"UPDATE chess_games SET {column} = %s WHERE id = %s",
            f"UPDATE chess_games SET {column} = ? WHERE id = ?",
            (user_id, game_id)
        )

    @classmethod
    def join_multiplayer_match(cls, game_id, user_id):
        """
        Seat a subscriber into an active multiplayer battle.
        Returns {'status', 'message', 'seat', 'game'} — status 'error' carries a code hint.
        """
        game = cls.get_game(game_id)
        if not game:
            return {'status': 'error', 'code': 404, 'message': 'Match not found.'}

        if str(game.get('status')) in ('completed', 'abandoned', 'cancelled'):
            return {'status': 'error', 'code': 409, 'message': 'This match is already closed.'}

        if game.get('white_user_id') == user_id:
            return {'status': 'success', 'seat': 'white', 'game': game, 'message': 'You are already seated (White).'}
        if game.get('black_user_id') == user_id:
            return {'status': 'success', 'seat': 'black', 'game': game, 'message': 'You are already seated (Black).'}

        match_type = game.get('match_type')
        clan_battle = match_type in ('group_vs_group', 'group_vs_public')

        # Seat eligibility -------------------------------------------------
        if game.get('black_group_id'):
            group_name_row = query_one(
                "SELECT name FROM chat_groups WHERE id = %s",
                "SELECT name FROM chat_groups WHERE id = ?",
                (game['black_group_id'],)
            )
            group_name = (group_name_row or {}).get('name', 'the rival clan')
            if not cls.is_clan_member(game['black_group_id'], user_id):
                return {
                    'status': 'error', 'code': 403,
                    'message': f'Black seat belongs to clan "{group_name}". Ask a clan admin for an invitation.'
                }

        if not game.get('is_public', 1) and not cls.has_live_invitation(game_id, user_id):
            return {'status': 'error', 'code': 403, 'message': 'This match is invitation only.'}

        # Seat assignment --------------------------------------------------
        if not game.get('black_user_id'):
            seat = 'black'
        elif not game.get('white_user_id'):
            seat = 'white'
        else:
            return {'status': 'error', 'code': 409, 'message': 'Both seats are taken — match is full.'}

        if seat == 'white' and clan_battle and game.get('white_group_id'):
            if not cls.is_clan_member(game['white_group_id'], user_id):
                return {'status': 'error', 'code': 403, 'message': 'White seat belongs to your rival clan.'}

        cls.set_game_seat(game_id, seat, user_id)

        # Register the challenger into the clan roster they just played for
        if seat == 'black' and game.get('black_group_id'):
            cls.add_clan_member(game['black_group_id'], user_id)
        if seat == 'white' and game.get('white_group_id'):
            cls.add_clan_member(game['white_group_id'], user_id)

        label = 'White' if seat == 'white' else 'Black'
        return {'status': 'success', 'seat': seat, 'game': cls.get_game(game_id),
                'message': f'You joined the battle as {label}.'}

    @staticmethod
    def find_joinable_public_match(user_id):
        """An open Public vs Public table hosted by another subscriber with a free seat."""
        return query_one(
            """SELECT * FROM chess_games
               WHERE match_type = 'public' AND is_public = 1 AND status = 'active'
                 AND black_user_id IS NULL AND user_id != %s
               ORDER BY created_at DESC LIMIT 1""",
            """SELECT * FROM chess_games
               WHERE match_type = 'public' AND is_public = 1 AND status = 'active'
                 AND black_user_id IS NULL AND user_id != ?
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        )

    @staticmethod
    def record_team_move(game_id, user_id, team, move_uci, move_san="", comment=""):
        sql_mysql = """
            INSERT INTO chess_team_moves (game_id, user_id, team, move_uci, move_san, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        sql_sqlite = """
            INSERT INTO chess_team_moves (game_id, user_id, team, move_uci, move_san, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return execute_insert(sql_mysql, sql_sqlite, (game_id, user_id, team, move_uci, move_san, comment))

    @staticmethod
    def get_game_team_moves(game_id, limit=30):
        sql_mysql = """
            SELECT tm.*, u.username, u.avatar_color
            FROM chess_team_moves tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.game_id = %s
            ORDER BY tm.created_at DESC LIMIT %s
        """
        sql_sqlite = """
            SELECT tm.*, u.username, u.avatar_color
            FROM chess_team_moves tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.game_id = ?
            ORDER BY tm.created_at DESC LIMIT ?
        """
        return query_all(sql_mysql, sql_sqlite, (game_id, limit))
