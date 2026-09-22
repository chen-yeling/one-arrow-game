import pygame
import sys


# ============================================================
# 一箭又一箭
# 一个简单的 Pygame 网格箭头消除游戏
# ============================================================


# -------------------------
# 1. 初始化 Pygame
# -------------------------
pygame.init()

# 游戏窗口大小
WIDTH = 800
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭")

# 游戏帧率
clock = pygame.time.Clock()
FPS = 60


# -------------------------
# 2. 颜色
# -------------------------
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)
BLUE = (70, 130, 220)
LIGHT_BLUE = (220, 235, 255)
GREEN = (70, 180, 100)
RED = (220, 70, 70)
LIGHT_RED = (255, 220, 220)
YELLOW = (240, 190, 50)


# -------------------------
# 3. 字体
# -------------------------
# 使用 Windows 字体文件直接加载，避免 SysFont 在部分 Windows 环境下的兼容问题
def load_font(size):
    font_paths = [
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for path in font_paths:
        try:
            return pygame.font.Font(path, size)
        except (pygame.error, OSError):
            pass
    # 如果以上中文字体都不存在，使用 Pygame 默认字体，至少保证游戏可以启动
    return pygame.font.Font(None, size)

font_large = load_font(52)
font_title = load_font(42)
font_middle = load_font(30)
font_normal = load_font(24)
font_small = load_font(20)

# -------------------------
# 4. 游戏基本参数
# -------------------------
ROWS = 6
COLS = 6

CELL_SIZE = 70

BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE

BOARD_X = (WIDTH - BOARD_WIDTH) // 2
BOARD_Y = 150

MAX_MISTAKES = 3


# ============================================================
# 5. 三个固定关卡
# ============================================================

# 每个箭头使用：
# (行, 列, 方向)
#
# 方向：
# "up"    = ↑
# "down"  = ↓
# "left"  = ←
# "right" = →

LEVELS = [

    # ---------------------------------------------------------
    # 第1关：熟悉关
    # 10 个箭头，四个方向比较均衡。
    # 不再使用简单的同向排列，而是设置多处交叉阻挡。
    # 玩家需要先找到当前没有被挡住的箭头。
    # ---------------------------------------------------------
    [
        (2, 5, "up"),
        (5, 3, "left"),
        (4, 2, "left"),
        (3, 2, "down"),
        (0, 0, "right"),
        (1, 0, "up"),
        (5, 1, "up"),
        (2, 3, "down"),
        (0, 3, "down"),
        (3, 1, "right"),
    ],

    # ---------------------------------------------------------
    # 第2关：进阶关
    # 14 个箭头，四个方向分别为 4/4/3/3。
    # 箭头分散在棋盘各处，不采用整排同方向箭头。
    # 多个箭头之间存在交叉阻挡，需要连续判断消除顺序。
    # ---------------------------------------------------------
    [
        (4, 4, "down"),
        (0, 4, "down"),
        (4, 3, "up"),
        (1, 4, "left"),
        (0, 0, "down"),
        (4, 5, "up"),
        (2, 5, "up"),
        (1, 5, "right"),
        (0, 3, "left"),
        (2, 2, "right"),
        (3, 1, "left"),
        (1, 3, "up"),
        (2, 0, "right"),
        (2, 1, "down"),
    ],

    # ---------------------------------------------------------
    # 第3关：挑战关
    # 18 个箭头，四个方向分别为 5/5/4/4。
    # 箭头数量明显增加，但同方向箭头分散。
    # 通过多层交叉阻挡形成较长的消除链。
    # 玩家不能只观察一个方向，需要综合判断行和列。
    # ---------------------------------------------------------
    [
        (3, 2, "down"),
        (4, 3, "up"),
        (0, 2, "left"),
        (0, 5, "down"),
        (1, 3, "right"),
        (0, 4, "right"),
        (1, 2, "up"),
        (5, 2, "down"),
        (5, 5, "down"),
        (0, 1, "down"),
        (4, 5, "left"),
        (5, 1, "right"),
        (3, 3, "left"),
        (3, 4, "left"),
        (2, 0, "right"),
        (2, 3, "up"),
        (5, 4, "up"),
        (3, 0, "up"),
    ]
]


# ============================================================
# 6. 箭头类
# ============================================================

class Arrow:
    """
    表示棋盘中的一个箭头。
    """

    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction

        # 是否正在飞出
        self.flying = False

        # 飞行动画的进度
        self.fly_progress = 0

        # 是否正在碰撞动画
        self.shaking = False

        # 碰撞动画阶段：0=向前冲，1=撞击停顿，2=退回原位
        self.collision_phase = 0

        # 碰撞动画中箭头相对原位置的移动距离
        self.collision_progress = 0

        # 本次碰撞需要向前移动的实际距离
        # 会根据阻碍箭头所在格子动态计算，确保真的“碰到”
        self.collision_distance = 20

        # 撞击后的短暂停顿
        self.impact_timer = 0

        # 撞击闪烁时间，用于让碰撞更加明显
        self.impact_flash_timer = 0

        # 碰撞动画剩余时间（保留用于晃动效果）
        self.shake_timer = 0

    def get_rect(self):
        """
        返回箭头所在棋盘格的矩形区域。
        """

        x = BOARD_X + self.col * CELL_SIZE
        y = BOARD_Y + self.row * CELL_SIZE

        return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    def get_center(self):
        """
        返回箭头中心位置。
        """

        rect = self.get_rect()

        return rect.centerx, rect.centery

    def update(self):
        """
        更新箭头动画。
        """

        # 飞行动画
        if self.flying:
            self.fly_progress += 12

            # 飞出一定距离以后删除
            if self.fly_progress > 500:
                return True

        # ----------------------------------------------------
        # 碰撞动画：前进 -> 真正接触 -> 撞击停顿 -> 退回
        # ----------------------------------------------------
        if self.shaking:

            # 阶段 0：沿箭头方向向阻碍箭头移动
            if self.collision_phase == 0:
                self.collision_progress += 5

                # 到达阻碍箭头的接触位置
                if self.collision_progress >= self.collision_distance:
                    self.collision_progress = self.collision_distance
                    self.collision_phase = 1
                    self.impact_timer = 5
                    self.impact_flash_timer = 8

            # 阶段 1：已经“撞上”，短暂停留
            elif self.collision_phase == 1:
                self.impact_timer -= 1

                if self.impact_timer <= 0:
                    self.collision_phase = 2

            # 阶段 2：沿原路退回
            elif self.collision_phase == 2:
                self.collision_progress -= 5

                if self.collision_progress <= 0:
                    self.collision_progress = 0
                    self.shaking = False
                    self.collision_phase = 0

        if self.impact_flash_timer > 0:
            self.impact_flash_timer -= 1

        return False

    def draw(self, surface):
        """
        绘制箭头。
        """

        center_x, center_y = self.get_center()

        # -------------------------
        # 飞行动画
        # -------------------------
        if self.flying:

            if self.direction == "up":
                center_y -= self.fly_progress

            elif self.direction == "down":
                center_y += self.fly_progress

            elif self.direction == "left":
                center_x -= self.fly_progress

            elif self.direction == "right":
                center_x += self.fly_progress

        # -------------------------
        # 碰撞动画位移
        # -------------------------
        if self.shaking:

            # 箭头沿自己的方向向前移动，直到箭头尖端接触阻碍箭头
            if self.direction == "up":
                center_y -= self.collision_progress
            elif self.direction == "down":
                center_y += self.collision_progress
            elif self.direction == "left":
                center_x -= self.collision_progress
            elif self.direction == "right":
                center_x += self.collision_progress

            # 撞击瞬间增加轻微垂直晃动，表现“撞击”
            if self.collision_phase == 1:
                shake = 4 if (self.impact_timer % 2 == 0) else -4
                if self.direction in ("up", "down"):
                    center_x += shake
                else:
                    center_y += shake

        # 碰撞时变红
        if self.shaking:
            color = RED
        else:
            color = BLUE

        # 箭头大小
        size = 20

        # -------------------------
        # 绘制箭头
        # -------------------------

        if self.direction == "up":

            pygame.draw.line(
                surface,
                color,
                (center_x, center_y + size),
                (center_x, center_y - size),
                7
            )

            pygame.draw.polygon(
                surface,
                color,
                [
                    (center_x, center_y - size - 5),
                    (center_x - 13, center_y - 2),
                    (center_x + 13, center_y - 2)
                ]
            )

        elif self.direction == "down":

            pygame.draw.line(
                surface,
                color,
                (center_x, center_y - size),
                (center_x, center_y + size),
                7
            )

            pygame.draw.polygon(
                surface,
                color,
                [
                    (center_x, center_y + size + 5),
                    (center_x - 13, center_y + 2),
                    (center_x + 13, center_y + 2)
                ]
            )

        elif self.direction == "left":

            pygame.draw.line(
                surface,
                color,
                (center_x + size, center_y),
                (center_x - size, center_y),
                7
            )

            pygame.draw.polygon(
                surface,
                color,
                [
                    (center_x - size - 5, center_y),
                    (center_x - 2, center_y - 13),
                    (center_x - 2, center_y + 13)
                ]
            )

        elif self.direction == "right":

            pygame.draw.line(
                surface,
                color,
                (center_x - size, center_y),
                (center_x + size, center_y),
                7
            )

            pygame.draw.polygon(
                surface,
                color,
                [
                    (center_x + size + 5, center_y),
                    (center_x + 2, center_y - 13),
                    (center_x + 2, center_y + 13)
                ]
            )


# ============================================================
# 7. 游戏类
# ============================================================

class Game:

    def __init__(self):

        # 当前关卡
        self.level = 0

        # 游戏状态
        # start   = 开始界面
        # playing = 游戏中
        # win     = 通关
        # lose    = 失败
        # finish  = 全部通关
        self.state = "start"

        # 箭头列表
        self.arrows = []

        # 剩余失误次数
        self.mistakes = MAX_MISTAKES

        # 碰撞文字显示时间
        self.collision_message_timer = 0

        # 最后一次失误后的失败等待标记。
        # 为 True 时必须等本次碰撞动画完整结束后才能进入失败页面。
        self.pending_lose = False

        # 加载第一关
        self.load_level(0)

    # --------------------------------------------------------
    # 加载关卡
    # --------------------------------------------------------

    def load_level(self, level_number):

        self.level = level_number

        self.arrows = []

        # 根据关卡数据创建箭头
        for row, col, direction in LEVELS[level_number]:

            arrow = Arrow(row, col, direction)

            self.arrows.append(arrow)

        # 重置失误次数
        self.mistakes = MAX_MISTAKES

        self.collision_message_timer = 0
        self.pending_lose = False

    # --------------------------------------------------------
    # 开始游戏
    # --------------------------------------------------------

    def start_game(self):

        self.load_level(0)

        self.state = "playing"

    # --------------------------------------------------------
    # 重新开始当前关
    # --------------------------------------------------------

    def restart_level(self):

        self.load_level(self.level)

        self.state = "playing"

    # --------------------------------------------------------
    # 获取鼠标点击的箭头
    # --------------------------------------------------------

    def get_clicked_arrow(self, mouse_pos):

        for arrow in self.arrows:

            # 飞出或正在碰撞动画中的箭头不能再次点击
            if arrow.flying or arrow.shaking:
                continue

            rect = arrow.get_rect()

            if rect.collidepoint(mouse_pos):
                return arrow

        return None

    # --------------------------------------------------------
    # 判断箭头前方是否有其他箭头
    # --------------------------------------------------------

    def is_blocked(self, arrow):

        """
        判断当前箭头前进方向上是否存在其他箭头。

        因为采用单格网格，所以只需要检查
        同一行或者同一列。
        """

        row = arrow.row
        col = arrow.col

        # 向上
        if arrow.direction == "up":

            for other in self.arrows:

                if other is arrow:
                    continue

                if other.flying:
                    continue

                # 同一列，并且位于当前箭头上方
                if other.col == col and other.row < row:
                    return True

        # 向下
        elif arrow.direction == "down":

            for other in self.arrows:

                if other is arrow:
                    continue

                if other.flying:
                    continue

                # 同一列，并且位于当前箭头下方
                if other.col == col and other.row > row:
                    return True

        # 向左
        elif arrow.direction == "left":

            for other in self.arrows:

                if other is arrow:
                    continue

                if other.flying:
                    continue

                # 同一行，并且位于当前箭头左边
                if other.row == row and other.col < col:
                    return True

        # 向右
        elif arrow.direction == "right":

            for other in self.arrows:

                if other is arrow:
                    continue

                if other.flying:
                    continue

                # 同一行，并且位于当前箭头右边
                if other.row == row and other.col > col:
                    return True

        return False

    # --------------------------------------------------------
    # 找到当前箭头前方最近的阻碍箭头
    # --------------------------------------------------------

    def get_nearest_obstacle(self, arrow):

        candidates = []

        for other in self.arrows:

            if other is arrow or other.flying:
                continue

            if arrow.direction == "up" and other.col == arrow.col and other.row < arrow.row:
                candidates.append(other)

            elif arrow.direction == "down" and other.col == arrow.col and other.row > arrow.row:
                candidates.append(other)

            elif arrow.direction == "left" and other.row == arrow.row and other.col < arrow.col:
                candidates.append(other)

            elif arrow.direction == "right" and other.row == arrow.row and other.col > arrow.col:
                candidates.append(other)

        if not candidates:
            return None

        # 按网格距离选择最近的箭头
        if arrow.direction in ("up", "down"):
            return min(candidates, key=lambda a: abs(a.row - arrow.row))
        else:
            return min(candidates, key=lambda a: abs(a.col - arrow.col))

    # --------------------------------------------------------
    # 计算碰撞时的实际移动距离
    # --------------------------------------------------------

    def get_collision_distance(self, arrow, obstacle):

        if obstacle is None:
            return 20

        # 箭头绘制时，尖端距离中心约 25 像素。
        # 因此需要根据两箭头中心距离计算，让前方箭头的尖端
        # 移动到阻碍箭头的可视边缘，而不是只移动固定距离。
        if arrow.direction in ("up", "down"):
            center_distance = abs(obstacle.row - arrow.row) * CELL_SIZE
        else:
            center_distance = abs(obstacle.col - arrow.col) * CELL_SIZE

        # 对同向箭头，前方箭头的后端约在中心 20 像素处；
        # 对相向箭头，两边都是尖端，约 25+25 像素。
        if arrow.direction == obstacle.direction:
            obstacle_reach = 20
        else:
            obstacle_reach = 25

        distance = center_distance - 25 - obstacle_reach

        # 相邻格时：
        # 相向箭头约 20 像素即可接触；同向箭头约 25 像素即可接触。
        return max(5, distance)

    # --------------------------------------------------------
    # 点击箭头
    # --------------------------------------------------------

    def click_arrow(self, arrow):

        # 如果最后一次失误已经发生，正在等待碰撞动画结束后进入失败页面，
        # 不再接受任何新的点击，防止失误次数继续变成负数。
        if self.mistakes <= 0 or self.pending_lose:
            return

        # 如果当前有箭头正在碰撞动画中，暂时不接受新的箭头点击，
        # 防止碰撞动画还没结束就触发下一次操作。
        if any(a.shaking for a in self.arrows):
            return

        # 如果箭头正在飞出，不处理
        if arrow.flying:
            return

        # 判断是否被阻挡
        blocked = self.is_blocked(arrow)

        if blocked:

            # 找到当前方向上最近的阻碍箭头，计算真正的接触距离
            obstacle = self.get_nearest_obstacle(arrow)

            # 开始“前进 -> 撞击 -> 退回”动画
            arrow.shaking = True
            arrow.collision_phase = 0
            arrow.collision_progress = 0
            arrow.collision_distance = self.get_collision_distance(arrow, obstacle)
            arrow.impact_timer = 0
            arrow.impact_flash_timer = 0
            arrow.shake_timer = 30

            # 失误次数减少
            self.mistakes -= 1

            # 显示碰撞提示
            self.collision_message_timer = 60

            # 失误次数耗尽
            # 不立即切换失败页面，而是等待本次“前进 -> 撞击 -> 退回”
            # 动画播放完成后再进入失败页面。
            if self.mistakes <= 0:

                # 只设置“等待失败”标记，不使用固定倒计时。
                # 因为不同箭头之间的碰撞距离不同，动画时长也不同；
                # 固定倒计时可能先结束，导致永远无法进入失败页面。
                self.pending_lose = True

        else:

            # 没有阻挡，开始飞出
            arrow.flying = True
            arrow.fly_progress = 0

    # --------------------------------------------------------
    # 更新游戏
    # --------------------------------------------------------

    def update(self):

        if self.state != "playing":
            return

        # 保存需要删除的箭头
        remove_arrows = []

        for arrow in self.arrows:

            should_remove = arrow.update()

            if should_remove:
                remove_arrows.append(arrow)

        # 删除已经飞出棋盘的箭头
        for arrow in remove_arrows:

            if arrow in self.arrows:
                self.arrows.remove(arrow)

        # 碰撞文字计时
        if self.collision_message_timer > 0:
            self.collision_message_timer -= 1

        # 如果最后一次失误已经发生，必须先让本次碰撞动画完整播放，
        # 再进入失败页面。这里不再使用固定帧数倒计时，
        # 而是直接等待所有碰撞动画结束，避免动画较长时“卡死”。
        if self.pending_lose:

            # 当前碰撞动画还没结束：继续播放，不切换页面。
            if any(a.shaking for a in self.arrows):
                return

            # 碰撞动画已经完整结束，再进入失败页面。
            self.pending_lose = False
            self.state = "lose"
            return

        # 判断是否全部清除
        if len(self.arrows) == 0:

            if self.level < len(LEVELS) - 1:

                self.state = "win"

            else:

                self.state = "finish"

    # --------------------------------------------------------
    # 绘制开始界面
    # --------------------------------------------------------

    def draw_start_screen(self):

        screen.fill(LIGHT_BLUE)

        # 标题
        title = font_large.render(
            "一箭又一箭",
            True,
            BLACK
        )

        screen.blit(
            title,
            (
                WIDTH // 2 - title.get_width() // 2,
                150
            )
        )

        # 副标题
        subtitle = font_middle.render(
            "点击没有阻挡的箭头，让它飞出棋盘",
            True,
            DARK_GRAY
        )

        screen.blit(
            subtitle,
            (
                WIDTH // 2 - subtitle.get_width() // 2,
                230
            )
        )

        # 开始按钮
        start_rect = pygame.Rect(
            WIDTH // 2 - 110,
            330,
            220,
            65
        )

        pygame.draw.rect(
            screen,
            BLUE,
            start_rect,
            border_radius=12
        )

        text = font_middle.render(
            "开始游戏",
            True,
            WHITE
        )

        screen.blit(
            text,
            (
                start_rect.centerx - text.get_width() // 2,
                start_rect.centery - text.get_height() // 2
            )
        )

        # 规则
        rule1 = font_small.render(
            "箭头前方没有其他箭头时，可以成功飞出",
            True,
            BLACK
        )

        rule2 = font_small.render(
            "如果被阻挡，点击会消耗一次失误机会",
            True,
            BLACK
        )

        screen.blit(
            rule1,
            (
                WIDTH // 2 - rule1.get_width() // 2,
                440
            )
        )

        screen.blit(
            rule2,
            (
                WIDTH // 2 - rule2.get_width() // 2,
                475
            )
        )

    # --------------------------------------------------------
    # 绘制游戏界面
    # --------------------------------------------------------

    def draw_game_screen(self):

        screen.fill(WHITE)

        # -------------------------
        # 顶部标题
        # -------------------------

        title = font_title.render(
            "一箭又一箭",
            True,
            BLACK
        )

        screen.blit(
            title,
            (40, 30)
        )

        # 当前关卡
        level_text = font_normal.render(
            f"第 {self.level + 1} 关",
            True,
            BLACK
        )

        screen.blit(
            level_text,
            (330, 45)
        )

        # 剩余箭头
        arrow_count_text = font_normal.render(
            f"剩余箭头：{len(self.arrows)}",
            True,
            BLACK
        )

        screen.blit(
            arrow_count_text,
            (480, 45)
        )

        # 失误次数
        mistake_text = font_normal.render(
            f"剩余失误：{self.mistakes}",
            True,
            RED if self.mistakes == 1 else BLACK
        )

        screen.blit(
            mistake_text,
            (40, 100)
        )

        # -------------------------
        # 绘制棋盘
        # -------------------------

        board_rect = pygame.Rect(
            BOARD_X,
            BOARD_Y,
            BOARD_WIDTH,
            BOARD_HEIGHT
        )

        pygame.draw.rect(
            screen,
            (245, 245, 245),
            board_rect
        )

        # 绘制网格
        for row in range(ROWS + 1):

            y = BOARD_Y + row * CELL_SIZE

            pygame.draw.line(
                screen,
                GRAY,
                (BOARD_X, y),
                (BOARD_X + BOARD_WIDTH, y),
                2
            )

        for col in range(COLS + 1):

            x = BOARD_X + col * CELL_SIZE

            pygame.draw.line(
                screen,
                GRAY,
                (x, BOARD_Y),
                (x, BOARD_Y + BOARD_HEIGHT),
                2
            )

        # -------------------------
        # 绘制箭头
        # -------------------------

        for arrow in self.arrows:
            arrow.draw(screen)

        # -------------------------
        # 碰撞提示
        # -------------------------

        if self.collision_message_timer > 0:

            collision_text = font_middle.render(
                "碰撞！前方有其他箭头",
                True,
                RED
            )

            screen.blit(
                collision_text,
                (
                    WIDTH // 2 - collision_text.get_width() // 2,
                    610
                )
            )

        # -------------------------
        # 重新开始按钮
        # -------------------------

        restart_rect = pygame.Rect(
            WIDTH - 170,
            625,
            130,
            45
        )

        pygame.draw.rect(
            screen,
            DARK_GRAY,
            restart_rect,
            border_radius=8
        )

        restart_text = font_small.render(
            "重新开始",
            True,
            WHITE
        )

        screen.blit(
            restart_text,
            (
                restart_rect.centerx - restart_text.get_width() // 2,
                restart_rect.centery - restart_text.get_height() // 2
            )
        )

    # --------------------------------------------------------
    # 绘制通关界面
    # --------------------------------------------------------

    def draw_win_screen(self):

        screen.fill(LIGHT_BLUE)

        title = font_large.render(
            f"第 {self.level + 1} 关通关！",
            True,
            GREEN
        )

        screen.blit(
            title,
            (
                WIDTH // 2 - title.get_width() // 2,
                180
            )
        )

        message = font_middle.render(
            "恭喜你清除了本关所有箭头",
            True,
            BLACK
        )

        screen.blit(
            message,
            (
                WIDTH // 2 - message.get_width() // 2,
                270
            )
        )

        next_rect = pygame.Rect(
            WIDTH // 2 - 110,
            360,
            220,
            60
        )

        pygame.draw.rect(
            screen,
            BLUE,
            next_rect,
            border_radius=10
        )

        next_text = font_middle.render(
            "下一关",
            True,
            WHITE
        )

        screen.blit(
            next_text,
            (
                next_rect.centerx - next_text.get_width() // 2,
                next_rect.centery - next_text.get_height() // 2
            )
        )

        restart_rect = pygame.Rect(
            WIDTH // 2 - 110,
            440,
            220,
            55
        )

        pygame.draw.rect(
            screen,
            DARK_GRAY,
            restart_rect,
            border_radius=10
        )

        restart_text = font_normal.render(
            "重新开始本关",
            True,
            WHITE
        )

        screen.blit(
            restart_text,
            (
                restart_rect.centerx - restart_text.get_width() // 2,
                restart_rect.centery - restart_text.get_height() // 2
            )
        )

    # --------------------------------------------------------
    # 绘制失败界面
    # --------------------------------------------------------

    def draw_lose_screen(self):

        screen.fill(LIGHT_RED)

        title = font_large.render(
            "本关失败",
            True,
            RED
        )

        screen.blit(
            title,
            (
                WIDTH // 2 - title.get_width() // 2,
                180
            )
        )

        message = font_middle.render(
            "失误次数已经用完",
            True,
            BLACK
        )

        screen.blit(
            message,
            (
                WIDTH // 2 - message.get_width() // 2,
                270
            )
        )

        restart_rect = pygame.Rect(
            WIDTH // 2 - 110,
            370,
            220,
            60
        )

        pygame.draw.rect(
            screen,
            BLUE,
            restart_rect,
            border_radius=10
        )

        restart_text = font_middle.render(
            "重新开始",
            True,
            WHITE
        )

        screen.blit(
            restart_text,
            (
                restart_rect.centerx - restart_text.get_width() // 2,
                restart_rect.centery - restart_text.get_height() // 2
            )
        )

    # --------------------------------------------------------
    # 绘制全部通关界面
    # --------------------------------------------------------

    def draw_finish_screen(self):

        screen.fill(LIGHT_BLUE)

        title = font_large.render(
            "全部通关！",
            True,
            GREEN
        )

        screen.blit(
            title,
            (
                WIDTH // 2 - title.get_width() // 2,
                180
            )
        )

        message = font_middle.render(
            "恭喜你完成了全部三个关卡",
            True,
            BLACK
        )

        screen.blit(
            message,
            (
                WIDTH // 2 - message.get_width() // 2,
                270
            )
        )

        restart_rect = pygame.Rect(
            WIDTH // 2 - 110,
            370,
            220,
            60
        )

        pygame.draw.rect(
            screen,
            BLUE,
            restart_rect,
            border_radius=10
        )

        restart_text = font_middle.render(
            "重新游戏",
            True,
            WHITE
        )

        screen.blit(
            restart_text,
            (
                restart_rect.centerx - restart_text.get_width() // 2,
                restart_rect.centery - restart_text.get_height() // 2
            )
        )

    # --------------------------------------------------------
    # 处理鼠标点击
    # --------------------------------------------------------

    def handle_mouse_click(self, mouse_pos):

        # -------------------------
        # 开始界面
        # -------------------------

        if self.state == "start":

            start_rect = pygame.Rect(
                WIDTH // 2 - 110,
                330,
                220,
                65
            )

            if start_rect.collidepoint(mouse_pos):

                self.start_game()

        # -------------------------
        # 游戏界面
        # -------------------------

        elif self.state == "playing":

            # 重新开始按钮
            restart_rect = pygame.Rect(
                WIDTH - 170,
                625,
                130,
                45
            )

            if restart_rect.collidepoint(mouse_pos):

                self.restart_level()

                return

            # 点击箭头
            arrow = self.get_clicked_arrow(mouse_pos)

            if arrow is not None:

                self.click_arrow(arrow)

        # -------------------------
        # 通关界面
        # -------------------------

        elif self.state == "win":

            # 下一关
            next_rect = pygame.Rect(
                WIDTH // 2 - 110,
                360,
                220,
                60
            )

            if next_rect.collidepoint(mouse_pos):

                self.load_level(self.level + 1)

                self.state = "playing"

                return

            # 重新开始本关
            restart_rect = pygame.Rect(
                WIDTH // 2 - 110,
                440,
                220,
                55
            )

            if restart_rect.collidepoint(mouse_pos):

                self.restart_level()

        # -------------------------
        # 失败界面
        # -------------------------

        elif self.state == "lose":

            restart_rect = pygame.Rect(
                WIDTH // 2 - 110,
                370,
                220,
                60
            )

            if restart_rect.collidepoint(mouse_pos):

                self.restart_level()

        # -------------------------
        # 全部通关
        # -------------------------

        elif self.state == "finish":

            restart_rect = pygame.Rect(
                WIDTH // 2 - 110,
                370,
                220,
                60
            )

            if restart_rect.collidepoint(mouse_pos):

                self.start_game()

    # --------------------------------------------------------
    # 绘制当前界面
    # --------------------------------------------------------

    def draw(self):

        if self.state == "start":

            self.draw_start_screen()

        elif self.state == "playing":

            self.draw_game_screen()

        elif self.state == "win":

            self.draw_win_screen()

        elif self.state == "lose":

            self.draw_lose_screen()

        elif self.state == "finish":

            self.draw_finish_screen()


# ============================================================
# 8. 主程序
# ============================================================

def main():

    # 创建游戏对象
    game = Game()

    # 游戏主循环
    running = True

    while running:

        # -------------------------
        # 处理事件
        # -------------------------

        for event in pygame.event.get():

            # 点击窗口关闭按钮
            if event.type == pygame.QUIT:

                running = False

            # 鼠标点击
            elif event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    game.handle_mouse_click(event.pos)

        # -------------------------
        # 更新游戏
        # -------------------------

        game.update()

        # -------------------------
        # 绘制画面
        # -------------------------

        game.draw()

        # 更新窗口
        pygame.display.flip()

        # 控制帧率
        clock.tick(FPS)

    # 退出 Pygame
    pygame.quit()

    sys.exit()


# ============================================================
# 9. 程序入口
# ============================================================

if __name__ == "__main__":
    main()
