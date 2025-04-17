from tkinter.ttk import Combobox

import numpy as np
import os
import tkinter
from tkinter import *

import pandas as pd
import itertools

import HelperFunction as HF
import WidgetHelper as WH

# fd = pathlib.Path(__file__).parent.resolve()
fd = os.getcwd()
Window_Size = [1280, 1280]
fw = int(Window_Size[0]/2)
fh = int(Window_Size[1]/2)
fs = (fw/200, fh/200)

class CharacteristicAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Characteristic Curve")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+450}x{int(2*fh/3)+100}")
        self.window.resizable(True, True)

        self.filepath = ""
        self.OffsetCalibration = BooleanVar()
        self.ReadType, self.dFormat = StringVar(), StringVar()
        self.ImageSize_Row = IntVar()
        self.ImageSize_Col = IntVar()

        self.FOI_Start, self.FOI_End, self.ROI_Left, self.ROI_Right, self.ROI_Up, self.ROI_Dn =\
            IntVar(), IntVar(), IntVar(), IntVar(), IntVar(), IntVar()
        self.InputData = np.array([], dtype=np.float64)
        self.dark_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)
        self.Average = np.array([], dtype=np.float64)

        self.DarkSubtraction = BooleanVar()
        self.ExposuredFrame, self.DarkFrame = IntVar(), IntVar()

        self.Division_Column, self.Division_Row = IntVar(), IntVar()

        self.Output = np.array([], dtype=np.float64)
        self.FlipOutput = BooleanVar()
        self.ColumnName = ["0"]
        self.__main__()

    def Open_Path(self):

        self.filepath = WH.ButtonClickedEvent.Open_Path(fd)
        self.label1.configure(text=f"{self.filepath[-40:]}")

    def Read_Image(self, r, c, fp, ReadType):

        if not hasattr(self, 'ImageWidget'):
            self.ImageWidget = WH.Plotting.MakeFigureWidget(self.ImagePlotFrame, fs)

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        if ReadType.split(" ")[-1] == "Folders":
            # self.InputData = np.array([], dtype=np.float64)
            InputData = []
            for ffpath in WH.ButtonClickedEvent.Read_Folders(fp):

                InputData = HF.NumpyHelper.AppendList(InputData, self.Read_Image(r, c, ffpath, "Files")[0])
                asdf = 1
            self.InputData = HF.NumpyHelper.npArray_DifferentSizeList(InputData)
            self.ColumnName = os.listdir(self.filepath)
            RepresentativeData = self.InputData.copy()

            WH.UIConfiguration.set_text(self.Entry4_1, '1')
            WH.UIConfiguration.set_text(self.Entry4_2, f"{int(RepresentativeData.shape[1])}")


        # Missed Direct Callback from Button Clicked
        elif ReadType.split(" ")[-1] == "Files":

            Image_Size = [r, c]
            InputData = WH.ButtonClickedEvent.Read_Folder(fp, self.dFormat.get()[1:], np.uint16, Image_Size)

            RepresentativeData = InputData
            self.frame_average = HF.DataProcessing.TemporalAverage(RepresentativeData)

            WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)
            WH.UIConfiguration.set_text(self.Entry4_1, '1')
            WH.UIConfiguration.set_text(self.Entry4_2, f"{int(len(RepresentativeData))}")
            WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
            WH.UIConfiguration.set_text(self.Entry5_1_2, f"{int(RepresentativeData.shape[-1]) - 1}")
            WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
            WH.UIConfiguration.set_text(self.Entry5_2_2, f'{int(RepresentativeData.shape[-2]) - 1}')

            InputData = np.expand_dims(InputData, axis=0)
            self.InputData = InputData.copy()
            return InputData

    def Show_ROI(self, ax, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        ROI1 = np.array([int(self.ROI_Left.get()), int(self.ROI_Dn.get())])
        ROI2 = np.array([int(self.ROI_Right.get()), int(self.ROI_Up.get())])

        Frame = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)
        Frame = WH.ButtonClickedEvent.Set_FOI(Frame, FOI)
        self.ROI_Data = Frame
        if Frame.ndim == 4:
            WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data[-1]), ax)
        else:
            WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), ax)

    def ShowBlock(self, ax, Frame, data, row, col, xROI_s, xROI_e, yROI_s, yROI_e):
        if Frame.ndim == 4:
            Frame = Frame[-1]

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(Frame), ax)
        WH.Plotting.DrawDivision(ax, HF.DataProcessing.TemporalAverage(Frame), row, col)
        self.OutputDivision(ax, data, row, col)
        self.Coordinates = HF.DataProcessing.MakeCoordinate(xROI_s, xROI_e, yROI_s, yROI_e, col, row)

    def Calculate(self, ax1, ax2, ROIData):

        Average = HF.DataProcessing.SpatialAverage(ROIData)

        if ROIData.ndim == 4:
            WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data[-1]), ax1)
            Average = Average[-1]
        else:
            WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(ROIData), ax1)

        # ROIData = HF.DataProcessing.Array2Maskedarray(ROIData)

        WH.Plotting.Show2DPlot(ax2, np.arange(Average.shape[0]) + 1, Average, c='r', label='Time Response',
                               cla=True, xlabel='Frame Number $n^{th}$', ylabel='Pixel Value [DN]')

    def GetExposuredFrame(self, ax, ROIData, n):
        if ROIData.ndim == 4:
            Average = HF.DataProcessing.SpatialAverage(ROIData[-1, n - 1])
            self.ExposuredImage = ROIData[:, n - 1]

        elif ROIData.ndim == 3:
            Average = HF.DataProcessing.SpatialAverage(ROIData[n - 1])
            self.ExposuredImage = ROIData[n - 1]

        WH.Plotting.ShowPoint(ax, n, Average, c='b', label='Exposed')
        asdf = 1

    def GetDarkFrame(self, ax, ROIData, n):
        Average = HF.DataProcessing.SpatialAverage(ROIData[n-1])
        WH.Plotting.ShowPoint(ax, n, Average, c='g', label='Dark')
        if self.ExposuredImage.shape[0] == 1:
            self.ExposuredImage = np.append(self.ExposuredImage, ROIData[n - 1][np.newaxis, :], axis=0)
        else:
            self.ExposuredImage[1] = ROIData[n-1]

    def OutputDivision(self, ax, data, row, col):
        data = HF.DataProcessing.Array2Maskedarray(data)
        temp =  np.array([], dtype=np.float64)

        for data_now in data:
            avg = WH.ButtonClickedEvent.Average(ax, data_now, row, col)
            temp = HF.NumpyHelper.AppendArray(temp, avg, newaxis=-1)
        self.Output = temp

    def SaveBTNEvent(self, data):

        WH.ButtonClickedEvent.Save_csv(self.filepath, data)

    def SaveClipboardBTNEvent(self, data, col, ind, doflip):
        if doflip:
            data = np.flip(data, axis=-1)
            list(reversed(col))
        df = pd.DataFrame(data, index =ind, columns=col)
        WH.ButtonClickedEvent.SaveClipboard(df)
        asdf = 1

    def __main__(self):

        self.InputFrame = tkinter.Frame(self.window, width=fw, height=fh+100)
        self.InputFrame.grid(column=0, row=0)
        self.ImagePlotFrame = tkinter.Frame(self.InputFrame, bg='white', width=fw/2, height=fh/2)
        self.ImagePlotFrame.grid(column=0, row=0)
        self.ROIPlotFrame = tkinter.Frame(self.InputFrame, bg='white', width=fw / 2, height=fh / 2)
        self.ROIPlotFrame.grid(column=1, row=0)

        self.InputinfoFrame = tkinter.Frame(self.InputFrame, width=fw, height=100)
        self.InputinfoFrame.grid(column=0, row=1, columnspan = 2)

        col0 = 0
        Entry0Span = 1

        self.ReadCBox = Combobox(self.InputinfoFrame, width = 8, textvariable = self.ReadType, state="readonly", values=[" Open Folders", " Open Files"])
        self.ReadCBox.set(" Open Folders")
        self.ReadCBox.grid(column = col0, row = 2, columnspan=Entry0Span)

        col = col0 + Entry0Span

        Entry1Span = 1
        self.label1 = tkinter.Label(self.InputinfoFrame)
        self.label1.grid(column=col, row=1, columnspan=3)
        self.Button1 = tkinter.Button(self.InputinfoFrame, textvariable=self.ReadType, command=self.Open_Path)
        self.Button1.grid(column=col, row=2)
        self.Label1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size(Row, Col)')
        self.Label1_1.grid(column=col, row=3)
        self.Label1_2 = tkinter.Label(self.InputinfoFrame, text = 'Format')
        self.Label1_2.grid(column=col, row=4)
        col = col + Entry1Span

        Entry2Span = 2
        self.Button2 = tkinter.Button(self.InputinfoFrame, text='Read File', command=lambda: self.Read_Image(int(self.ImageSize_Row.get()),
                                                                                                             int(self.ImageSize_Col.get()),
                                                                                                             self.filepath,
                                                                                                             self.ReadType.get()))
        self.Button2.grid(column=col, row=2, columnspan=Entry2Span)
        self.Entry2_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ImageSize_Row, relief="ridge")
        self.Entry2_1_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry2_1_1, '1280')
        self.Entry2_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ImageSize_Col, relief="ridge")
        self.Entry2_1_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry2_1_2, '1280')
        self.FormatCBox = Combobox(self.InputinfoFrame, width = 4, textvariable = self.dFormat, state="readonly", values=[" raw", " tif"])
        self.FormatCBox.set(" raw")
        self.FormatCBox.grid(column = col, row = 4, columnspan=Entry2Span)
        col = col + Entry2Span

        Entry3span = 0
        # self.Label3 = tkinter.Label(self.InputinfoFrame)
        # self.Label3.grid(column=col, row = 1, columnspan=10)
        # self.Button3 = tkinter.Button(self.InputinfoFrame, text='Dark File', command=self.Dark_Image)
        # self.Button3.grid(column=col, row=2, columnspan=Entry3span)
        col = col + Entry3span

        Entry4Span = 2
        self.Entry4_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_Start, relief="ridge")
        self.Entry4_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry4_1, '0')
        self.Entry4_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_End, relief="ridge")
        self.Entry4_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry4_2, '0')
        self.Button4 = tkinter.Button(self.InputinfoFrame, text='Frame')
        self.Button4["state"] = 'disable'
        self.Button4.grid(column=col, row=2, columnspan=Entry4Span)
        col = col + Entry4Span

        Entry5Span = 2
        self.Entry5_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Left, relief="ridge")
        self.Entry5_1_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        self.Entry5_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Right, relief="ridge")
        self.Entry5_1_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry5_1_2, '0')
        self.Entry5_2_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Dn, relief="ridge")
        self.Entry5_2_1.grid(column=col, row=4)
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        self.Entry5_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Up, relief="ridge")
        self.Entry5_2_2.grid(column=col+1, row=4)
        WH.UIConfiguration.set_text(self.Entry5_2_2, '0')

        self.Button5 = tkinter.Button(self.InputinfoFrame, text='ROI (Left, Right \n Down, Up)')
        self.Button5["state"] = "disable"
        self.Button5.grid(column=col, row=2, columnspan=Entry5Span)
        col = col + Entry5Span

        Entry6Span = 3
        self.Button6 = tkinter.Button(self.InputinfoFrame, text='Show ROI', command=lambda: self.Show_ROI(self.ROIWidget, self.InputData.copy()))
        self.Button6.grid(column=col, row=2, columnspan=Entry6Span)
        self.Label6_1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size')
        self.Label6_1_1.grid(column=col, row=3)
        self.Label6_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        self.Label6_2_1.grid(column=col, row=4)
        self.Label6_3_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Left, Right)')
        self.Label6_3_1.grid(column=col, row=5)
        self.Label6_4_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Down, Up')
        self.Label6_4_1.grid(column=col, row=6)
        self.Label6_1_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Row)
        self.Label6_1_2.grid(column=col+1, row=3)
        self.Label6_2_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_Start)
        self.Label6_2_2.grid(column=col+1, row=4)
        self.Label6_3_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Left)
        self.Label6_3_2.grid(column=col+1, row=5)
        self.Label6_4_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Dn)
        self.Label6_4_2.grid(column=col+1, row=6)
        self.Label6_1_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Col)
        self.Label6_1_3.grid(column=col+2, row=3)
        self.Label6_2_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_End)
        self.Label6_2_3.grid(column=col+2, row=4)
        self.Label6_3_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Right)
        self.Label6_3_3.grid(column=col+2, row=5)
        self.Label6_4_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Up)
        self.Label6_4_3.grid(column=col+2, row=6)
        col = col + Entry6Span

        Entry7Span = 1
        self.Button7 = tkinter.Button(self.InputinfoFrame, text='Calculate',
                                      command=lambda: self.Calculate(self.ImageWidget, self.ROIWidget,
                                                                     self.ROI_Data.copy()
                                                                     ))
        self.Button7.grid(column=col, row=2, columnspan=Entry7Span)
        col = col + Entry7Span

        Entry8Span = 1
        self.Button8 = tkinter.Button(self.InputinfoFrame, text='Exposured Frame #',
                                      command=lambda: self.GetExposuredFrame(self.ROIWidget, self.ROI_Data.copy(),
                                                                             self.ExposuredFrame.get())
                                      )
        self.Button8.grid(column=col, row=2, columnspan=Entry8Span)
        self.Entry8_1 = tkinter.Entry(self.InputinfoFrame, width=6, textvariable=self.ExposuredFrame, relief="ridge")
        self.Entry8_1.grid(column=col, row=3)
        self.CheckButton8_2 = tkinter.Checkbutton(self.InputinfoFrame, text="Dark Subtraction",
                                                    variable=self.DarkSubtraction,
                                                    command=lambda: WH.UIConfiguration.ButtonState(
                                                        [self.Entry9_1, self.Button9], self.DarkSubtraction.get()))
        self.CheckButton8_2.grid(column=col, row=4, columnspan=Entry8Span)
        self.DarkSubtraction.set(False)
        col = col + Entry8Span

        Entry9Span = 1
        self.Button9 = tkinter.Button(self.InputinfoFrame, text='Dark Frame #',
                                      command=lambda: self.GetDarkFrame(self.ROIWidget, self.ROI_Data.copy(),
                                                                        self.DarkFrame.get())
                                      )
        self.Button9.grid(column=col, row=2, columnspan=Entry9Span)
        self.Entry9_1 = tkinter.Entry(self.InputinfoFrame, width=6, textvariable=self.DarkFrame, relief="ridge")
        self.Entry9_1.grid(column=col, row=3)
        WH.UIConfiguration.ButtonState([self.Entry9_1, self.Button9], self.DarkSubtraction.get())
        col = col + Entry9Span

        Entry10Span = 2
        self.Label10_1_1 = tkinter.Label(self.InputinfoFrame, text='Column')
        self.Label10_1_1.grid(column = col, row = 3)
        self.Label10_2_1 = tkinter.Label(self.InputinfoFrame, text='Row')
        self.Label10_2_1.grid(column = col, row = 4)

        self.Entry10_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Column, relief="ridge")
        self.Entry10_1_2.grid(column=col + 1, row=3)
        self.Entry10_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Row, relief="ridge")
        self.Entry10_2_2.grid(column=col + 1, row=4)

        self.Button10 = tkinter.Button(self.InputinfoFrame, text='Division',
                                      command=lambda: self.ShowBlock(self.ImageWidget, self.ROI_Data.copy(), self.ExposuredImage.copy(), int(self.Division_Row.get()), int(self.Division_Column.get()),
                                                                     self.ROI_Left.get(), self.ROI_Right.get(), self.ROI_Dn.get(), self.ROI_Up.get()))
        self.Button10.grid(column=col, row=2, columnspan=Entry10Span)
        col = col + Entry10Span

        Entry11Span = 1
        self.Button11 = tkinter.Button(self.InputinfoFrame, text='Save Image', command=lambda: self.SaveBTNEvent(self.Output))
        self.Button11.grid(column=col, row=2, columnspan=Entry11Span)
        self.Button11_2 = tkinter.Button(self.InputinfoFrame, text='Save Clipboard', command=lambda: self.SaveClipboardBTNEvent(self.Output, self.ColumnName, self.Coordinates, self.FlipOutput.get()))
        self.Button11_2.grid(column=col, row=3)
        self.CheckButton11_3 = tkinter.Checkbutton(self.InputinfoFrame, text="Flip Data", variable=self.FlipOutput)
        self.CheckButton11_3.grid(column=col, row=4, columnspan=Entry11Span)

        col = col + Entry11Span


if __name__ == '__main__':
    window = tkinter.Tk()
    CharacteristicAnalysis(window)
    window.mainloop()