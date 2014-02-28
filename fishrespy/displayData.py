from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import math
import numpy as np
from matplotlib.ticker import NullFormatter

class DisplayData:
    """
    Display data in spreadsheet like window.
    Data format is dictionary of lists, each list refers to
    one row of data, or list of lists
    """
    def __init__(self, root, data):
        self.root = root
        self.root.title('Results')
        self.root.minsize(550, 620)
        self.root.maxsize(550, 620)

        #Configure canvas
        self.canvas = Canvas(self.root, width = 530, height = 600)

        #Configure frame for canvas
        self.canvasFrame = Frame(self.canvas, background = 'black')
        #configure scrollbars
        self.vscrollbar = ttk.Scrollbar(self.root, orient = 'vertical', command = self.canvas.yview)
        self.hscrollbar = ttk.Scrollbar(self.root, orient = 'horizontal', command = self.canvas.xview)

        self.canvas.configure(yscrollcommand = self.vscrollbar.set, xscrollcommand = self.hscrollbar.set)
        self.canvas.grid(row = 0, column = 0)
        self.vscrollbar.grid(row = 0, column = 1, sticky = (N, S))
        self.hscrollbar.grid(row = 1, column = 0, sticky = (W, E))

        self.canvasFrame.bind('<Configure>', self.onFrameConfigure)

        self.dataFrame = Frame(self.canvasFrame, background = 'black')
        self.dataFrame.grid(column = 1, row = 1)
        self.headerFrame = Frame(self.canvasFrame, background = 'black')
        self.headerFrame.grid(column = 1, row = 0)

        self.canvas.create_window((0, 0), window = self.canvasFrame, anchor = 'nw')

        #create header labels, configure to generate default header
        self.header = ['','slope','R2','start','MO2','mass', 'meanTemp', 'sdTemp']

        #data components
        self.data = data
        self.nrows = len(data)
        self.ncols = len(data[0])
        self.widgets = []
        self.cell_vals = {}
        self.cell_width = 10

        self.createHeader()
        self.createRowLabels()
        self.createCells()
        self.createMenu()

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion = self.canvas.bbox('all'))

    def createHeader(self):
        for c in range(len(self.header)):
            label = ttk.Label(self.headerFrame, text = self.header[c], width = self.cell_width)
            label.grid(row = 0, column = c + 1, padx = 1, pady = 1)

    def createRowLabels(self):
        for r in range(self.nrows):
            label = ttk.Label(self.dataFrame, text = str(r + 1), width = self.cell_width)
            label.grid(row = r, column = 0, padx = 1, pady = 1)

    def createCells(self):
        for r in range(self.nrows):
            curr_row = []
            for c in range(self.ncols):
                self.cell_vals[str(r) + str(c)] = DoubleVar()
                self.cell_vals[str(r) + str(c)].set(self.data[r][c])
                entry = ttk.Entry(self.dataFrame, width = self.cell_width, textvariable = self.cell_vals[str(r) + str(c)])
                entry.grid(row = r, column = c + 1)
                curr_row.append(entry)
            self.widgets.append(curr_row)

    def createMenu(self):
        menubar = Menu(self.root)
        menufile = Menu(menubar)
        menuplot = Menu(menubar)
        menubar.add_cascade(menu = menufile, label = 'File')
        menubar.add_cascade(menu = menuplot, label = 'Plot')
        menufile.add_command(label = 'Save', command = self.save_file)
        menufile.add_command(label = 'Close', command = self.close_file)
        menuplot.add_command(label = 'Timeseries', command = self.plot_ts)
        menuplot.add_command(label = 'Histogram', command = self.plot_hist)
        self.root.config(menu = menubar)

    def save_file(self):
        file = filedialog.asksaveasfilename(filetypes = [('Text Files', '*.csv')], defaultextension = '.csv')
        self.write_data(file)

    def close_file(self):
        self.root.destroy()

    def write_data(self, file):
        """Writes output from _storeMO2() to .csv file with header. File is
           path to destination.
        """
        with open(file, 'w', newline = '') as f:
            w = csv.writer(f)
            header = ['slope', 'R2', 'start', 'MO2', 'mass', 'meanTemp', 'sdTemp']
            w.writerow(header)
            for row in range(len(self.data)):
                line = self.data[row]
                w.writerow(line)

    def round_up(self, x, base = 50):
            return int(math.ceil(x / float(base)) * base)

    def set_ts(self, ax, x, y, label):
        ax.plot(y, x)
        ax.set_ylabel(label, fontsize = 10)

    def plot_ts(self):
        m = list()
        d = list()
        r = list()
        s = list()
        t = list()
        for i in range(len(self.data)):
            m.append(self.data[i][3])
            dt = datetime.strptime(self.data[i][2], '%d/%m/%y %H:%M:%S')
            d.append(dt)
            r.append(self.data[i][1])
            s.append(self.data[i][0])
            t.append(self.data[i][5])

        fig = plt.figure()
        fig.subplots_adjust(hspace = 0.8)

        ax = fig.add_subplot(411)
        self.set_ts(ax, m, d, 'MO2\n(mgO2$^{-1}$kg$^{-1}$h)')
        ax.set_ylim(0, self.round_up(max(m)))

        bx = fig.add_subplot(412)
        self.set_ts(bx, r, d, 'R$^2$')
        bx.set_yticks(np.arange(math.floor(min(r)*100)/100, 1, 0.01))

        cx = fig.add_subplot(413)
        self.set_ts(cx, s, d, 'Slope')
        cx.ticklabel_format(style = 'sci', scilimits = (0,0), axis = 'y')

        dx = fig.add_subplot(414)
        self.set_ts(dx, t, d, 'Temp ($^\circ$C)')
        dx.set_xlabel('Time of Day', fontsize = 10)
        dx.set_ylim(min(t) - 0.5, max(t) + 0.5)

        plt.show()

    def set_hist(self, ax, x, xlabel):
        bin_size = math.ceil(len(x) / 5)
        na = max(plt.hist(x, bin_size)[0])
        ax.set_xlabel(xlabel, fontsize = 10)
        ax.set_yticks(np.arange(0, self.round_up(na, base = 10) + 10, 10))
        for tick in ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(10)
        for tick in ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(10)

    def plot_hist(self):
        m = list()
        r = list()
        s = list()
        t = list()
        for i in range(len(self.data)):
            m.append(self.data[i][3])
            r.append(self.data[i][1])
            s.append(self.data[i][0])
            t.append(self.data[i][5])

        fig = plt.figure()
        fig.subplots_adjust(hspace = 0.8)
        fig.text(0.05, 0.52, 'Count').set_rotation(90)

        ax = fig.add_subplot(411)
        self.set_hist(ax, m, 'MO2 (mgO2$^{-1}$kg$^{-1}$h)')

        bx = fig.add_subplot(412)
        self.set_hist(bx, r, 'R$^2$')

        cx = fig.add_subplot(413)
        self.set_hist(cx, s, 'Slope')

        dx = fig.add_subplot(414)
        self.set_hist(dx, t, 'Temp ($^\circ$C)')

        plt.show()

def main():
    data = []
    for i in range(100):
        data.append([0]*7)

    root = Tk()
    view = DisplayData(root, data)
    root.mainloop()

if __name__ == '__main__':
    main()
