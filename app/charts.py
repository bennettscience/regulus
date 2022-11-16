import base64
from io import BytesIO

# matplotlib has to be opened without the GUI event loop connection to run on the server.
# see https://stackoverflow.com/questions/51188461/using-pyplot-close-crashes-the-flask-app
import matplotlib

matplotlib.use("agg")
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


class Chart:
    def __init__(self, series, labels=None):
        # Accept a series as list of tuples with the (x, y) defined
        self.series = series
        self.labels = labels

    def create_pie_figure(self):
        fig = Figure(figsize=(4.0, 3.0))
        labels = self.labels
        sizes = self.series

        colors = ["#32c192", "#e9164f"]

        px = 1 / plt.rcParams["figure.dpi"]

        ax1 = fig.subplots()
        ax1.pie(sizes, labels=labels, colors=colors, startangle=90)
        ax1.axis("equal")

        return fig

    def pie(self):
        fig = self.create_pie_figure()
        output = BytesIO()
        fig.savefig(output, format="png")
        output.seek(0)
        data = base64.b64encode(output.getbuffer()).decode("ascii")
        FigureCanvas(fig).print_png(output)
        return data
