'''
  @ Date: 2020-11-28 17:23:04
  @ Author: Qing Shuai
  @ LastEditors: Qing Shuai
  @ LastEditTime: 2021-03-28 22:19:34
  @ FilePath: /EasyMocap/easymocap/mytools/vis_base.py
'''
import cv2
import numpy as np
import json

def generate_colorbar(N = 20, cmap = 'jet'):
    bar = ((np.arange(N)/(N-1))*255).astype(np.uint8).reshape(-1, 1)
    colorbar = cv2.applyColorMap(bar, cv2.COLORMAP_JET).squeeze()
    if False:
        colorbar = np.clip(colorbar + 64, 0, 255)
    import random
    random.seed(666)
    index = [i for i in range(N)]
    random.shuffle(index)
    rgb = colorbar[index, :]
    rgb = rgb.tolist()
    return rgb

colors_bar_rgb = generate_colorbar(cmap='hsv')

colors_table = {
    'b': [0.65098039, 0.74117647, 0.85882353],
    '_pink': [.9, .7, .7],
    '_mint': [ 166/255.,  229/255.,  204/255.],
    '_mint2': [ 202/255.,  229/255.,  223/255.],
    '_green': [ 153/255.,  216/255.,  201/255.],
    '_green2': [ 171/255.,  221/255.,  164/255.],
    'r': [ 251/255.,  128/255.,  114/255.],
    '_orange': [ 253/255.,  174/255.,  97/255.],
    'y': [ 250/255.,  230/255.,  154/255.],
    '_r':[255/255,0,0],
    'g':[0,255/255,0],
    '_b':[0,0,255/255],
    'k':[0,0,0],
    '_y':[255/255,255/255,0],
    'purple':[128/255,0,128/255],
    'smap_b':[51/255,153/255,255/255],
    'smap_r':[255/255,51/255,153/255],
    'smap_b':[51/255,255/255,153/255],
}

def get_rgb(index):
    if isinstance(index, int):
        if index == -1:
            return (255, 255, 255)
        if index < -1:
            return (0, 0, 0)
        col = colors_bar_rgb[index%len(colors_bar_rgb)]
    else:
        col = colors_table.get(index, (1, 0, 0))
        col = tuple([int(c*255) for c in col[::-1]])
    return col

def plot_point(img, x, y, r, col, pid=-1):
    cv2.circle(img, (int(x+0.5), int(y+0.5)), r, col, -1)
    if pid != -1:
        cv2.putText(img, '{}'.format(pid), (int(x+0.5), int(y+0.5)), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)


def plot_line(img, pt1, pt2, lw, col):
    cv2.line(img, (int(pt1[0]+0.5), int(pt1[1]+0.5)), (int(pt2[0]+0.5), int(pt2[1]+0.5)),
        col, lw)

def plot_cross(img, x, y, col, width=10, lw=2):
    cv2.line(img, (int(x-width), int(y)), (int(x+width), int(y)), col, lw)
    cv2.line(img, (int(x), int(y-width)), (int(x), int(y+width)), col, lw)
    
def plot_bbox(img, bbox, pid, vis_id=True):
    # 画bbox: (l, t, r, b)
    x1, y1, x2, y2 = bbox[:4]
    x1 = int(round(x1))
    x2 = int(round(x2))
    y1 = int(round(y1))
    y2 = int(round(y2))
    color = get_rgb(pid)
    lw = max(img.shape[0]//300, 2)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, lw)
    if vis_id:
        cv2.putText(img, '{}'.format(pid), (x1, y1+20), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

def plot_keypoints(img, points, pid, config, vis_conf=False, use_limb_color=True, lw=2):
    for ii, (i, j) in enumerate(config['kintree']):
        if i >= len(points) or j >= len(points):
            continue
        pt1, pt2 = points[i], points[j]
        if use_limb_color:
            col = get_rgb(config['colors'][ii])
        else:
            col = get_rgb(pid)
        if pt1[-1] > 0.01 and pt2[-1] > 0.01:
            image = cv2.line(
                img, (int(pt1[0]+0.5), int(pt1[1]+0.5)), (int(pt2[0]+0.5), int(pt2[1]+0.5)),
                col, lw)
    for i in range(len(points)):
        x, y = points[i][0], points[i][1]
        c = points[i][-1]
        if c > 0.01:
            col = get_rgb(pid)
            cv2.circle(img, (int(x+0.5), int(y+0.5)), lw*2, col, -1)
            if vis_conf:
                cv2.putText(img, '{:.1f}'.format(c), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)

def plot_points2d(img, points2d, lines, lw=4, col=(0, 255, 0), putText=True):
    # 将2d点画上去
    for i, (x, y, v) in enumerate(points2d):
        if v < 0.01:
            continue
        c = col
        plot_cross(img, x, y, width=10, col=c, lw=lw)
        if putText:
            cv2.putText(img, '{}'.format(i), (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, c, 2)
    for i, j in lines:
        if points2d[i][2] < 0.01 or points2d[j][2] < 0.01:
            continue
        plot_line(img, points2d[i], points2d[j], 2, (255, 255, 255))

def merge(images, row=-1, col=-1, resize=False, ret_range=False):
    if row == -1 and col == -1:
        from math import sqrt
        row = int(sqrt(len(images)) + 0.5)
        col = int(len(images)/ row + 0.5)
        if row > col:
            row, col = col, row
        if len(images) == 8:
            # basketball 场景
            row, col = 2, 4
            images = [images[i] for i in [0, 1, 2, 3, 7, 6, 5, 4]]
        if len(images) == 7:
            row, col = 3, 3
        elif len(images) == 2:
            row, col = 2, 1
    height = images[0].shape[0]
    width = images[0].shape[1]
    ret_img = np.zeros((height * row, width * col, images[0].shape[2]), dtype=np.uint8) + 255
    ranges = []
    for i in range(row):
        for j in range(col):
            if i*col + j >= len(images):
                break
            img = images[i * col + j]
            # resize the image size
            img = cv2.resize(img, (width, height))
            ret_img[height * i: height * (i+1), width * j: width * (j+1)] = img
            ranges.append((width*j, height*i, width*(j+1), height*(i+1)))
    if resize:
        scale = min(1000/ret_img.shape[0], 1800/ret_img.shape[1])
        while ret_img.shape[0] > 2000:
            ret_img = cv2.resize(ret_img, None, fx=scale, fy=scale)
    if ret_range:
        return ret_img, ranges
    return ret_img