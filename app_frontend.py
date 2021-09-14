import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.express as px
from dash.dependencies import Input, Output, State
# Initialise the app

from app import APP
from app_backend import Annotator


pic_folder = dbc.Form(dbc.FormGroup([dbc.Input(placeholder="folders", id="pic_folder"),
                       dbc.Input(placeholder="filetypes", id="file_type"),
                       dbc.Button(type="submit")
                       ]), id="form_folder")

annotation_input = dbc.FormGroup([
                                    dbc.Label("Add Annotation"),
                                    dbc.Input(placeholder="2324X434", type="text", id="annot_input"),
                                    dbc.FormText("Use X if number cannot be determined"),
                                 ])

speed_items = dbc.FormGroup([dbc.Label("Current speed: n/a", id="annot_speed"),
                html.Hr(),
               dbc.Label("Expected end: n/a", id="annot_end"),
               html.Hr(),
                dbc.Label("Annotated: n/a", id="annot_stats"),
                html.Hr(),
               dbc.Button("Reset clock", color="success", id="btn_reset_clock"),
               dbc.Button("Store results", color="info", id="btn_store"),
               dcc.Interval(id="speed_checker", interval=60000, disabled=False),
               dcc.Interval(id="auto_storer", interval=600000, disabled=False)])

speed_card = dbc.Card([dbc.CardHeader("Speed Tester"),
                       dbc.CardBody(speed_items)], color="secondary")

btn_drop = dbc.Button("Drop", id="btn_drop", color="danger")

def get_layout():
    graph = dcc.Graph(id="fig-img", config={'modeBarButtonsToAdd':['drawline',
                                                'drawopenpath',
                                                'drawclosedpath',
                                                'drawcircle',
                                                'drawrect',
                                                'eraseshape'
                                               ]})
    anno_form = dbc.Form(annotation_input, id="form_annotate")
    base = dbc.Row([dbc.Col([dbc.Card([dbc.CardHeader("Select paths")], color="primary"),
                            pic_folder,
                            speed_card], width=4),
                    dbc.Col([dbc.Card([dbc.CardHeader("Picture annotation"),
                                       dbc.CardBody([graph])], color="primary"),
                             dbc.Row([dbc.Col(anno_form), dbc.Col(btn_drop)])], width=8)])
    return base

@APP.callback(Output("fig-img", "figure"),
              Input("form_folder", "n_submit"),
              Input("form_annotate", "n_submit"),
              Input("btn_drop", "n_clicks"),
              State("fig-img", "figure"),
              State("pic_folder", "value"),
              State("file_type", "value"),
              State("annot_input", "value"))
def update_figure(_, __, ___, fig, fdir, img_type, annot):
    print(fdir, img_type, annot)
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if input_id == "form_folder":
        ret = Annotator.reload(fdir)
        if ret is None:
            APP.conf_server.load_images(fdir, img_type)
        else:
            APP.conf_server = ret
    elif input_id == "form_annotate":
        if fig is None:
            raise Exception("Figure is not showing a picture.")
        APP.conf_server.annotate_cur_img(annot, fig["layout"]["shapes"])
    elif input_id == "btn_drop":
        APP.conf_server.ignore_img()

    APP.conf_server.load_next_img()

    return APP.conf_server.plot_current_img()

@APP.callback(Output("annot_speed", "children"), Output("annot_end", "children"),
              Output("annot_stats", "children"),
              Input("btn_reset_clock", "n_clicks"), Input("speed_checker", "n_intervals"),
              Input("auto_storer", "n_intervals"), Input("btn_store", "n_clicks"))
def update_clock(_, __, ___, ____):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if input_id == "btn_reset_clock":
        APP.conf_server.reset_clock()

    if input_id in ["auto_storer", "btn_store"]:
        APP.conf_server.store()

    try:
        speed, end, to_go = APP.conf_server.calc_speed_end()
        hours = int(end / 3600)
        minutes = int((int(end) % 3600)/60)
        seconds = int(end) % 60
        stat_txt = f"To be annotated: {to_go}/{len(APP.conf_server.image_fnames)}"
        return f"Current speed: {speed}", f"Finish in : {hours} h {minutes} m {seconds} s", stat_txt
    except Exception as err:
        print(err)
        return "Current speed: N/A", "Finish in: N/A", "Annotated: N/A"
