import math
import os
import random
import sys
import time

import pygame as pg

WIDTH, HEIGHT = 1100, 650
DELTA = {pg.K_UP: (0, -5), pg.K_DOWN: (0, 5), pg.K_LEFT: (-5, 0), pg.K_RIGHT: (5, 0)}
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(rct: pg.Rect) -> tuple[bool, bool]:
    """
    引数：こうかとんRect or 爆弾Rect
    戻り値：タプル（横方向判定結果, 縦方向判定結果）
    画面内ならTrue, 画面外ならFalse
    """
    horizon, vertical = True, True
    if rct.left < 0 or rct.right > WIDTH:
        horizon = False
    if rct.top < 0 or rct.bottom > HEIGHT:
        vertical = False
    return (horizon, vertical)


def gameover(screen: pg.Surface) -> None:
    """
    ゲームオーバー画面を5秒間表示する
    引数：画面Surface
    """
    black_img = pg.Surface((WIDTH, HEIGHT))
    pg.draw.rect(black_img, (0, 0, 0), (0, 0, WIDTH, HEIGHT))
    black_img.set_alpha(200)  # 半透明にして背景を少し見せる
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("Game Over", True, (255, 255, 255))
    txt_rct = txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    black_img.blit(txt, txt_rct)
    cry_img = pg.image.load("fig/8.png")
    for x in (txt_rct.left - 50, txt_rct.right + 50):  # 文字列の左右に泣きこうかとん
        black_img.blit(cry_img, cry_img.get_rect(center=(x, HEIGHT // 2)))
    screen.blit(black_img, [0, 0])
    pg.display.update()
    time.sleep(5)


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    時間とともに拡大・加速する爆弾の準備をする
    戻り値：タプル（10段階の大きさの爆弾Surfaceのリスト, 加速度のリスト）
    """
    bb_imgs = []
    for r in range(1, 11):
        bb_img = pg.Surface((20 * r, 20 * r))
        pg.draw.circle(bb_img, (255, 0, 0), (10 * r, 10 * r), 10 * r)
        bb_img.set_colorkey((0, 0, 0))
        bb_imgs.append(bb_img)
    bb_accs = [a for a in range(1, 11)]
    return bb_imgs, bb_accs


def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    """
    飛ぶ方向に応じたこうかとん画像を準備する
    戻り値：辞書（キー：合計移動量タプル, 値：その方向を向いたこうかとんSurface）
    """
    kk_img = pg.image.load("fig/3.png")  # 左向き
    kk_flip = pg.transform.flip(kk_img, True, False)  # 右向き
    kk_dict = {
        (0, 0): pg.transform.rotozoom(kk_img, 0, 0.9),  # キー押下がない場合
        (+5, 0): pg.transform.rotozoom(kk_flip, 0, 0.9),  # 右
        (+5, -5): pg.transform.rotozoom(kk_flip, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(kk_flip, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(kk_img, -45, 0.9),  # 左上
        (-5, 0): pg.transform.rotozoom(kk_img, 0, 0.9),  # 左
        (-5, +5): pg.transform.rotozoom(kk_img, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(kk_flip, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(kk_flip, -45, 0.9),  # 右下
    }
    return kk_dict


def calc_orientation(org: pg.Rect, dst: pg.Rect,
        current_xy: tuple[float, float]) -> tuple[float, float]:
    """
    orgから見てdstがある方向の速度ベクトルを求める
    引数1 org：爆弾Rect
    引数2 dst：こうかとんRect
    引数3 current_xy：計算前の速度ベクトル
    戻り値：ノルムが√50の速度ベクトル（距離が300未満なら計算前の速度ベクトル）
    """
    diff_x, diff_y = dst.centerx - org.centerx, dst.centery - org.centery
    norm = math.hypot(diff_x, diff_y)
    if norm < 300:  # 近すぎるときは慣性で進ませる
        return current_xy
    return diff_x / norm * math.sqrt(50), diff_y / norm * math.sqrt(50)


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    kk_imgs = get_kk_imgs()
    kk_img = kk_imgs[(0, 0)]
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200
    bb_imgs, bb_accs = init_bb_imgs()
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect()
    bb_rct.center = random.randint(10, WIDTH - 10), random.randint(10, HEIGHT - 10)
    vx, vy = 5, 5
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        screen.blit(bg_img, [0, 0])

        stage = min(tmr // 500, 9)  # 10秒ごとに1段階ずつ拡大・加速
        bb_img = bb_imgs[stage]
        bb_rct = bb_img.get_rect(center=bb_rct.center)
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))
        avx, avy = vx * bb_accs[stage], vy * bb_accs[stage]
        bb_rct.move_ip(avx, avy)
        horizon, vertical = check_bound(bb_rct)
        if not horizon:  # 横方向にはみ出たら反転
            vx *= -1
        if not vertical:  # 縦方向にはみ出たら反転
            vy *= -1
        screen.blit(bb_img, bb_rct)

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]
        for k, v in DELTA.items():
            if key_lst[k]:
                sum_mv[0] += v[0]
                sum_mv[1] += v[1]
        kk_rct.move_ip(sum_mv)
        if check_bound(kk_rct) != (True, True):  # 画面外なら更新前の位置に戻す
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])
        kk_img = kk_imgs[tuple(sum_mv)]
        screen.blit(kk_img, kk_rct)

        if kk_rct.colliderect(bb_rct):  # こうかとんと爆弾が衝突したら終了
            gameover(screen)
            return
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
