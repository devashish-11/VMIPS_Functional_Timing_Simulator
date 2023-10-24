import argparse
import glob

from matplotlib import pyplot as plt, ticker

from computeEngine import ComputeEngine
from dataEngine import DataEngine
from decode import Decode
from fetch import Fetch
from status import Status
import time
import os


class Config(object):
    def __init__(self, iodir, fileName="Config.txt"):
        self.filepath = os.path.abspath(os.path.join(iodir, fileName))
        self.parameters = {}  # dictionary of parameter name: value as strings.
        self.numberOfLanes = None
        self.addPipelineDepth = None
        self.mulPipelineDepth = None
        self.divPipelineDepth = None
        self.dataQueueDepth = None
        self.computeQueueDepth = None
        self.numberOfBanks = None
        self.vectorLoadStorePipelineDepth = None
        try:
            with open(self.filepath, 'r') as conf:
                self.parameters = {line.split('=')[0].strip(): int(line.split('=')[1].split('#')[0].strip()) for line in
                                   conf.readlines() if not (line.startswith('#') or line.strip() == '')}
            print("Config - Parameters loaded from file:", self.filepath)
            print("Config parameters:", self.parameters)
            self.parseParameters()
        except:
            print("Config - ERROR: Couldn't open file in path:", self.filepath)
            raise

    def parseParameters(self):
        self.dataQueueDepth = self.parameters["dataQueueDepth"]
        self.computeQueueDepth = self.parameters["computeQueueDepth"]
        self.numberOfBanks = self.parameters["vdmNumBanks"]
        self.vectorLoadStorePipelineDepth = self.parameters["vlsPipelineDepth"]
        self.numberOfLanes = self.parameters["numLanes"]
        self.addPipelineDepth = self.parameters["pipelineDepthAdd"]
        self.mulPipelineDepth = self.parameters["pipelineDepthMul"]
        self.divPipelineDepth = self.parameters["pipelineDepthDiv"]


class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16)  # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Data.txt"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [ins.split('#')[0].strip() for ins in insf.readlines() if
                                     not (ins.startswith('#') or ins.strip() == '')]
            print("IMEM - Instructions loaded from file:", self.filepath)
            # print("IMEM - Instructions:", self.instructions)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)
            raise


class Core:
    def __init__(self, config, imem, iodir):
        self.config = config
        self.imem = imem
        self.iodir = iodir
        self.compute = ComputeEngine(self.config.addPipelineDepth, self.config.mulPipelineDepth,
                                     self.config.divPipelineDepth, self.config.numberOfLanes)
        self.data = DataEngine(6, self.config.numberOfBanks, self.config.vectorLoadStorePipelineDepth)
        self.decode = Decode(self.config.computeQueueDepth, self.config.dataQueueDepth, 8, 8, self.compute, self.data)
        self.fetch = Fetch(self.imem.instructions, self.decode)
        self.compute.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.data.setFreeBusyBoard(self.decode.freeBusyBoard)
        self.clk = 1
        self.clks = []
        self.startTime = None
        self.endTime = None

    def run(self):
        print("Timing Simulation Started")
        self.startTime = time.time()
        while not (self.fetch.getStatus() == Status.COMPLETED and self.decode.isClear()):
            status1, instr = self.fetch.run()
            status2, computeInstr, dataInstr, scalarInstr = self.decode.run(instr)
            self.compute.run(computeInstr, self.fetch.getCurrentVectorLength())
            self.data.run(dataInstr)
            self.clk += 1
            # print(self.fetch.addr)

        self.endTime = time.time()
        print("Timing Simulation Successful")

    def printResult(self):
        time_difference = self.endTime - self.startTime
        minutes = str(int(time_difference // 60))
        seconds = str(int(time_difference % 60))
        # milliseconds = str(int((time_difference - int(time_difference)) * 1000))
        self.dataOutput = []

        self.dataOutput.append("================RESULT================")
        self.dataOutput.append("Clock Cycles: " + str(self.clk - 1))
        self.dataOutput.append("Time Elapsed: " + minutes + "m " + seconds + "s")
        self.dataOutput.append("======================================")
        for line in self.dataOutput:
            print(line)

    def dumpResult(self, fileName="Output.txt"):
        filepath = os.path.abspath(os.path.join(iodir, fileName))
        try:
            with open(filepath, 'w') as opf:
                lines = [str(line) + '\n' for line in self.dataOutput]
                opf.writelines(lines)
            print(fileName, "- Dumped output into output file in path:", filepath)
        except:
            print(fileName, "- ERROR: Couldn't open output file in path:", filepath)
        pass


def dumpSummary(iodir, cycles, fileName="Summary.txt"):
    cycles.insert(0, "================SUMMARY================")
    cycles.append("======================================")
    filepath = os.path.abspath(os.path.join(iodir, fileName))
    try:
        with open(filepath, 'w') as opf:
            lines = [str(line) + '\n' for line in cycles]
            opf.writelines(lines)
        print(fileName, "- Dumped summary into output file in path:", filepath)
    except:
        print(fileName, "- ERROR: Couldn't open output file in path:", filepath)
    pass


def readFiles(iodir):
    files = os.listdir(iodir)
    txt_files = [file_name for file_name in files if file_name.startswith("Config") and file_name.endswith(".txt")]
    txt_files.sort(key=lambda file_name: int(file_name[len('Config'):file_name.index('.')]))
    # print(txt_files)
    return txt_files


def parseArguments():
    parser = argparse.ArgumentParser(
        description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="IODir1", type=str,
                        help='Path to the folder containing the input files - resolved data')
    args = parser.parse_args()
    return os.path.abspath(args.iodir)

#
# def plotData(iodir, x, y, xlabel):
#     fig, ax = plt.subplots()
#
#     # Plot the data on the axis
#     ax.plot(x, y, '-o')
#
#     # Add labels to the axis and a title to the figure
#     ax.set_xlabel(xlabel)
#     ax.set_ylabel('Clock Cycles')
#     ax.set_title('Clock Cycles vs ' + xlabel)
#     ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
#     ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
#     filePath = os.path.abspath(
#         os.path.join(iodir, os.path.join("Plots", "fcLayer_" + xlabel.replace(' ', '_') + ".png")))
#     fig.savefig(filePath)
#     # fig.savefig("dotPdtPlots_" + xlabel.replace(' ', '_') + ".png")
#     plt.show()
#
#
# def plotSubPlot(iodir, x, y):
#     # Create a new figure and a grid of subplots with 3 rows and 1 column
#     fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(10, 10))
#     # Plot the data on the subplots
#     axs[0][0].plot(x[0:4], y[0:4])
#     axs[0][0].set_title('Clk Cycles vs ' + "Number of Vector Banks")
#     axs[0][0].set_xlabel("Number of Vector Banks")
#
#     axs[0][1].plot(x[4:8], y[4:8])
#     axs[0][1].set_title('Clk Cycles vs ' + "Compute Queue Depth")
#     axs[0][1].set_xlabel("Compute Queue Depth")
#
#     axs[1][0].plot(x[8:12], y[8:12])
#     axs[1][0].set_title('Clk Cycles vs ' + "Data Queue Depth")
#     axs[1][0].set_xlabel("Data Queue Depth")
#
#     axs[1][1].plot(x[12:], y[12:])
#     axs[1][1].set_title('Clk Cycles vs ' + "Number of Lanes")
#     axs[1][1].set_xlabel("Number of Lanes")
#
#     for a in axs:
#         for ax in a:
#             ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
#             ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
#             ax.set_ylabel('Performance')
#
#     # Adjust the layout of the subplots
#     fig.tight_layout()
#     figManager = plt.get_current_fig_manager()
#     figManager.full_screen_toggle()
#     filePath = os.path.abspath(
#         os.path.join(iodir, os.path.join("Plots", "fcLayer.png")))
#     fig.savefig(filePath, bbox_inches='tight')
#     # Show the plot
#     plt.show()


if __name__ == "__main__":
    iodir = parseArguments()
    txt_files = readFiles(iodir)
    imem = IMEM(iodir)
    cycles = []
    # noOfCycels = []
    for index, fileName in enumerate(txt_files):
        print("==============================")
        print("Running:", fileName)
        config = Config(iodir, fileName)
        core = Core(config, imem, iodir)
        core.run()
        core.printResult()
        core.dumpResult("Output" + str(index + 1) + ".txt")
        print("==============================")
        cycles.append(fileName[:fileName.index(".")] + " " + str(core.clk))
        # noOfCycels.append(core.clk)
    # plotData(iodir, [32, 16, 8, 4], noOfCycels[:4], "Number of Vector Memory Banks")
    # plotData(iodir, [16, 8, 4, 2], noOfCycels[4:8], "Depth of Compute Queue")
    # plotData(iodir, [16, 8, 4, 2], noOfCycels[8:12], "Depth of Data Queue")
    # plotData(iodir, [32, 16, 8, 4, 2], noOfCycels[12:], "Number of Lanes")
    # plotSubPlot(iodir,[32, 16, 8, 4, 16, 8, 4, 2, 16, 8, 4, 2, 32, 16, 8, 4, 2], noOfCycels)
    dumpSummary(iodir, cycles)
