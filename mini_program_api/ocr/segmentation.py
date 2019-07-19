import cv2
import numpy as np
import os
from sklearn.cluster import KMeans
import time



# import matplotlib.pyplot as plt


def non_max_suppression_fast(boxes, overlapThresh):
    # if there are no boxes, return an empty list
    if len(boxes) == 0:
        return []

    # if the bounding boxes integers, convert them to floats --
    # this is important since we'll be doing a bunch of divisions
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # initialize the list of picked indexes
    pick = []

    # grab the coordinates of the bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2] + x1
    y2 = boxes[:, 3] + y1

    # compute the area of the bounding boxes and sort the bounding
    # boxes by the bottom-right y-coordinate of the bounding box
    area = (x2 - x1 + 1) * (y2 - y1 + 1)

    idxs = np.argsort(y2)

    # keep looping while some indexes still remain in the indexes
    # list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the
        # index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # find the largest (x, y) coordinates for the start of
        # the bounding box and the smallest (x, y) coordinates
        # for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # compute the width and height of the bounding box

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # delete all indexes from the index list that have
        idxs = np.delete(idxs, np.concatenate(([last],
                                               np.where(overlap > overlapThresh)[0])))

    # return only the bounding boxes that were picked using the
    # integer data type
    return boxes[pick].astype("int")


def words_segment(gray, img_cut, DEBUG, distanceThresh=500):
    orig_img_cut = img_cut
    param_group = []
    WIDTH = len(gray[0])
    HEIGHT = len(gray)
    mser = cv2.MSER_create(_delta=5)
    gray_reverse = cv2.bitwise_not(gray)
    regions, boxes = mser.detectRegions(gray)
    # regions_r, boxes_r = mser.detectRegions(gray_reverse)
    indices = [i for (i, v) in enumerate(boxes) if v[3] > HEIGHT / 4 or v[2] < 5 or v[0] < 5 or v[0] + v[2] > WIDTH - 5]
    # indices_r = [i for (i, v) in enumerate(boxes_r) if v[3] > HEIGHT / 4]
    boxes = np.delete(boxes, indices, 0)
    # boxes_r = np.delete(boxes_r, indices_r, 0)
    # np.concatenate((boxes, boxes_r), axis=1)

    boxes = non_max_suppression_fast(boxes, 0.1)
    # if DEBUG:
    #     for box in boxes:
    #         cv2.rectangle(img_cut, (box[0], box[1]), (box[0]+box[2], box[3]+box[1]), (255, 0, 0), 2)
    try:
        dataSet = boxes[:, 2:4]
        kmeans = KMeans(n_clusters=3, random_state=0, max_iter=500).fit(dataSet)
        centers = kmeans.cluster_centers_
        # print("this is centers")
        # print(centers)
        picks = [[] for i in range(3)]
        for index, box in enumerate(boxes):
            x, y, w, h = box
            for center in centers:
                if ((w - center[0]) ** 2 + (h - center[1]) ** 2) < distanceThresh:
                    picks[kmeans.labels_[index]].append([box, 0])
                # cv2.rectangle(img, (x + x1, y), (x + x1 + w, y + h), (255, 0, 0), 2)

        for index_pick, pick in enumerate(picks):
            pick.sort(key=(lambda item: item[0][1]))
            for index_point, point in enumerate(pick):
                if index_point < len(pick) - 1:
                    if point[0][1] + point[0][3] + 2 * centers[index_pick][1] > pick[index_point + 1][0][1]:
                        point[1] = point[1] + 1

        params = []
        for i in range(3):
            index = 0
            while index < len(picks[i]):
                if picks[i][index][1] == 0:
                    index = index + 1
                    continue
                left = WIDTH
                right = 0
                top = picks[i][index][0][1]
                bottom = 0
                while index < len(picks[i]) and picks[i][index][1] != 0:
                    if picks[i][index][0][0] < left:
                        left = picks[i][index][0][0]
                    if picks[i][index][0][0] + picks[i][index][0][2] > right:
                        right = picks[i][index][0][0] + picks[i][index][0][2]
                    index = index + 1
                if index < len(picks[i]):
                    bottom = picks[i][index][0][1] + picks[i][index][0][3]
                else:
                    bottom = picks[i][index - 1][0][1] + picks[i][index - 1][0][3]

                flag = 0
                for index_param, param in enumerate(params):
                    if bottom <= param[2] or top >= param[3]:
                        continue
                    else:
                        params[index_param] = [min(param[0], left), max(param[1], right), min(param[2], top),
                                               max(param[3], bottom)]
                        flag = 1
                        break
                if flag == 0:
                    params.append([left, right, top, bottom])
                index = index + 1

        # print(params)
        params.sort(key=lambda param: param[2])
        new_params = []

        i = 0
        while i < len(params):
            candi = params[i]
            i = i + 1
            while i < len(params) and candi[3] + candi[1] - candi[0] > params[i][2]:
                candi = extend(candi, params[i])
                i = i + 1
            if (candi[1]-candi[0])*(candi[3]-candi[2])>500:
                new_params.append(candi)
        params = new_params
        if DEBUG:
            for param in params:
                cv2.rectangle(img_cut, (param[0], param[2]), (param[1], param[3]), (255, 0, 0), 2)
        print(params)
        for param in params:
            param_group.append(orig_img_cut[max(0, param[2] - 20):min(param[3] + 20, HEIGHT),
                               max(0, param[0] - 20):min(param[1] + 20, WIDTH)])
    finally:
        param_group.append(orig_img_cut)
        return param_group


def segment(pic,
            MIN_COUNT=200, RHO_THRES=50, THETA_THRES=30 / 52, THETA_OFFSET=10 / 52, DEBUG=0):
    """
    这个函数用于将书籍照片分割为单个的书籍，返回一个储存单本书的bytes数组
    :param imgpath:     图片的路径
    :param MIN_COUNT:   200 霍夫变换中计数器的最小阈值，用于筛选不合格的直线。这个值越大，越不明显的直线就会被消除
    :param RHO_THRES:   rho的收敛半径，在这一范围内的直线都会被视作一条直线。这个值越大，越大范围内的直线就会被视作一条直线
    :param THETA_THRES: theta的收敛角度，在这一角度内的直线会被视作一条直线。这个值越大，越大倾斜角度内的直线就会被视作一个直线
    :param THETA_OFFSET:theta的过滤角度，在这一个角度之外的直线不会被视作书籍的分割线。这个值越大，倾斜的越厉害的直线就会被视作分割线
    :param DEBUG:       如果使用DEBUG模式的话，会生成一些中间结果以及展示效果。比如边缘、分割线、cut输出
    :return:            返回一个cuts数组，每个元素表示切出来的图片数组
    """
    # ================= 霍夫变换 ==================
    #imgpath = "./test3.jpg"
    # img = cv2.imread(imgpath)
    img = cv2.imdecode(np.fromstring(pic, dtype=np.uint8), -1)

    IMG_HEIGHT = img.shape[0]
    IMG_WIDTH = img.shape[1]
    print("image shape(w,h):",IMG_WIDTH,IMG_HEIGHT,)
    img = cv2.resize(img,(1080,int(IMG_HEIGHT/IMG_WIDTH*1080)))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 灰度处理

    #if not os.path.exists("./output"):
    #    os.mkdir("./output")
    #dir_name = "./output/{0}".format()
    #os.mkdir(dir_name)

    #cv2.imwrite(dir_name + "/o_img.jpg", img)

    kernel = np.ones((9, 9), np.uint8)
    gray_open = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    # gray reverse
    # gray_reverse = cv2.bitwise_not(gray)
    # regions, boxes = mser.detectRegions(gray)
    # regions_r, boxes_r = mser.detectRegions(gray_reverse)
    # indices = [i for (i, v) in enumerate(boxes) if v[3] > IMG_HEIGHT / 2]
    # indices_r = [i for (i, v) in enumerate(boxes_r) if v[3] > IMG_HEIGHT / 2]
    # boxes= np.delete(boxes,indices,0)
    # boxes_r= np.delete(boxes_r,indices_r,0)
    # np.concatenate((boxes, boxes_r), axis=1)
    # boxes = non_max_suppression_fast(boxes, 0.4)

    edges = cv2.Canny(gray_open, 30, 90)  # 提取边缘
    lines = cv2.HoughLines(edges, 0.8, np.pi / 180, MIN_COUNT)  # 霍夫变换
    print("Hough change succeed...")
    # 输出文件

    # if DEBUG:
    #     cv2.imwrite(dir_name + "/edges.jpg", edges)
    #     cv2.imwrite(dir_name + "/gray_open.jpg", gray_open)
    # ================= 过滤及聚簇 ====================

    results = []  # results 保存直线的tho和theta信息

    for line in lines:
        rho, theta = line[0]
        if abs(theta) < THETA_OFFSET or abs(np.pi - theta) < THETA_OFFSET:  # 保证正斜率与负斜率都被考虑到
            found = 0
            if len(results) == 0:
                results.append(line[0])
            else:
                for result in results:
                    rho_diff = abs(abs(result[0]) - abs(rho))
                    if theta > np.pi / 2:
                        theta = np.pi - theta
                    theta_diff = abs(theta - result[1])
                    # theta_diff_pi = abs(theta-np.pi)
                    # if theta < theta_diff_pi: theta_diff = theta
                    # else : theta_diff = theta_diff_pi
                    if rho_diff < RHO_THRES and theta_diff < THETA_THRES:
                        found = 1
                        break
                if not found: results.append(line[0])

    results.sort(key=(lambda x: x[0]))  # 按照rho的大小排序

    print("Collection succeed...")

    # ================= 矩形裁剪 ==================
    # 极坐标转换为直角坐标系
    linesEndpoints = []  # linesEndpoints 保存矩形的两个端点的信息
    for result in results:
        rho, theta = result
        x1, y1, x2, y2 = changeToPolar(rho, theta, IMG_HEIGHT)
        linesEndpoints.append((x1, y1, x2, y2))

    # 防止线相交
    linesEndpoints.sort(key=lambda point: point[0])
    linesPoints = []
    preIndex = -1
    for index, endPoints in enumerate(linesEndpoints):
        if preIndex == -1:
            linesPoints.append((endPoints))
            preIndex = 0
        if (endPoints[2] > linesEndpoints[preIndex][2]) and min_gap(endPoints, linesEndpoints[preIndex],
                                                                    IMG_WIDTH / 50):
            linesPoints.append(endPoints)
            preIndex = index
        # print("remove!!!")

    cuts = []

    for index, endpoints in enumerate(linesPoints):
        if index < len(linesPoints) - 1:
            x1, y1, x2, y2 = endpoints
            x1_n, y1_n, x2_n, y2_n = linesPoints[index + 1]
            # 左边界
            left = np.min([x1, x2, x1_n, x2_n])
            if left < 0: left = 0  # 防止越界
            # 右边界
            right = np.max([x1, x2, x1_n, x2_n])
            if right > IMG_WIDTH: right = IMG_WIDTH
            # 切割
            src = np.array([[x1, y1], [x2, y2], [x1_n, y1_n], [x2_n, y2_n]], dtype="float32")
            imgSize = (int((x2_n + x1_n) / 2) - int((x2 + x1) / 2), y2)
            dst = np.array([[0, 0], [0, y2], [imgSize[0], 0], [imgSize[0], imgSize[1]]], dtype="float32")
            matrix = cv2.getPerspectiveTransform(src, dst)

            cut_resize = cv2.warpPerspective(img, matrix, imgSize)
            if len(cut_resize) < 15:
                continue
            gray_cut_resize = cv2.warpPerspective(gray, matrix, imgSize)
            # cut = img[:, left:right]

            cuts.append(words_segment(gray_cut_resize, cut_resize, DEBUG))
            # if DEBUG:
            #     cv2.imwrite(dir_name + "/cut_{0}.jpg".format(index), cut_resize)

    print("Cut change succeed...")
    # ================= 绘图及保存 ==================

    # if DEBUG:
    #     cv2.imwrite(dir_name + "/img.jpg", img)
    #     for index, endPoints in enumerate(linesPoints):
    #         x1, y1, x2, y2 = endPoints
    #         cv2.line(img, (x1, y1), (x2, y2), (0, 0, 100), 3)
    #     cv2.imwrite(dir_name + "/lines_fixed.jpg", img)
    #     for index, endPoints in enumerate(linesEndpoints):
    #         x1, y1, x2, y2 = endPoints
    #         cv2.line(img, (x1, y1), (x2, y2), (0, 0, 100), 3)
    #     cv2.imwrite(dir_name + "/lines.jpg", img)

    string_cuts = []

    for cut_group in cuts:
        temp_list = []
        for cut in cut_group:
            temp_list.append(cv2.imencode(".jpg", cut)[1].tostring())
        string_cuts.append(temp_list)
    return string_cuts


def changeToPolar(rho, theta, img_height):
    x1 = int(rho / np.cos(theta))
    y1 = 0
    x2 = int(x1 - img_height * np.tan(theta))
    y2 = img_height

    return x1, y1, x2, y2


def min_gap(point1, point2, gap):
    x1_middle = (point1[0] + point1[2]) / 2
    x2_middle = (point2[0] + point2[2]) / 2
    if abs(x2_middle - x1_middle) < gap:
        return False
    else:
        return True


if __name__ == "__main__":
    segment(DEBUG=1)


def extend(param1, param2):
    return [min(param1[0], param2[0]), max(param1[1], param2[1]),
            min(param1[2], param2[2]), max(param1[3], param2[3])]
