import glob
import os
import json
import time

import imageio
import pandas as pd
import numpy as np
import plotly.express as px


def xyxy_to_xywh(rect):
    w = rect["x1"] - rect["x0"]
    h = rect["y1"] - rect["y0"]
    return rect["x0"], rect["y0"], w, h

def create_annotation(annot, rectangles):
    if len(rectangles) != len(annot):
        raise Exception("All rectangles need to have an annotation.")

    x = np.array(list(map(lambda x: x["x0"], rectangles)))
    sorted_args = np.argsort(x)

    return [{"rect": xyxy_to_xywh(rectangles[i]), "class":annot[i]} for i in sorted_args]


class Annotator():
    def __init__(self):
        self.cur_img = None
        self.cur_img_path = None
        self.cur_img_num = None
        self.image_fnames = None
        self.last_shapes = None
        self.annotations = None
        self.project_dir = None
        self.t1_speed = None
        self.anno_num = None

    def store(self):
        if self.project_dir is None:
            return
        conf = {}
        conf["cur_img_path"] = self.cur_img_path
        conf["cur_img_num"] = self.cur_img_num
        conf["image_fnames"] = self.image_fnames
        conf["last_shapes"] = self.last_shapes
        conf["annotations"] = self.annotations
        conf["project_dir"] = self.project_dir

        jname = "annotator_conf.json"
        with open(os.path.join(self.project_dir, jname), "w") as fson:
            json.dump(conf, fson)

    @staticmethod
    def reload(fdir):
        fname = os.path.join(fdir, "annotator_conf.json")
        if os.path.exists(fname):
            with open(fname, "r") as fson:
                conf = json.load(fson)
            a = Annotator()
            a.cur_img_path = conf["cur_img_path"]
            a.cur_img_num = conf["cur_img_num"]
            a.image_fnames = conf["image_fnames"]
            a.last_shapes = conf["last_shapes"]
            a.annotations = conf["annotations"]
            a.project_dir = conf["project_dir"]
            a.cur_img = imageio.imread(a.cur_img_path)
            a.reset_clock()
            return a
        else:
            return None

    def load_images(self, fdir, img_types):
        if not os.path.exists(fdir):
            raise Exception("Path is not valid: ", fdir)

        self.image_fnames = glob.glob(os.path.join(fdir, img_types))
        self.image_fnames.sort(key=os.path.getmtime)
        self.annotations = {}
        self.project_dir = fdir
        self.reset_clock()

    def load_next_img(self):
        if self.image_fnames is None:
            raise Exception("No images to load. Please load file dir first.")

        if self.cur_img_path is None:
            self.cur_img_num = 0
        else:
            self.cur_img_num += 1

        self.cur_img_path = str(self.image_fnames[self.cur_img_num])
        self.cur_img = imageio.imread(self.cur_img_path)


    def plot_current_img(self):
        if self.cur_img is None:
            raise Exception("Please load img first.")

        fig = px.imshow(self.cur_img, color_continuous_scale='gray')
        # Define dragmode, newshape parameters, amd add modebar buttons
        fig.update_layout(
            dragmode='drawrect', # define dragmode
            newshape=dict(line_color='cyan'))
        if self.last_shapes is not None:
            fig.update_layout(shapes=self.last_shapes)
        return fig

    def annotate_cur_img(self, annot, shapes):
        rects = []
        for shape in shapes:
            if shape["type"] != "rect":
                continue
            rects.append(shape)
        self.annotations[self.cur_img_path] = create_annotation(annot, rects)
        self.last_shapes = shapes
        self.anno_num += 1

    def ignore_img(self):
        self.annotations[self.cur_img_path] = []
        self.anno_num += 1

    def reset_clock(self):
        self.anno_num = 0
        self.t1_speed = time.time()

    def calc_speed_end(self):
        if self.t1_speed is None or self.anno_num is None:
            raise Exception("Reset the clock first.")

        if self.anno_num == 0:
            raise Exception("Please annotate something.")

        t2 = time.time()
        speed = (t2 - self.t1_speed)/self.anno_num
        to_go = len(self.image_fnames) - len(self.annotations)
        end = to_go*speed
        return speed, end, to_go
