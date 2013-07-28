﻿#!/usr/bin/python
# -*- coding: UTF-8 -*-

from Config import Config
from Messages import Messages
from app.gui.Gui import Gui
from PDDemulate import PDDemulator
from PDDemulate import PDDEmulatorListener
from dumppattern import PatternDumper
import Tkinter

class KnittingApp(Tkinter.Tk):

    def __init__(self,parent=None):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        #self.startEmulator()
        
    def initialize(self):
        self.msg = Messages(self)
        self.patterns = []
        self.pattern = None
        self._cfg = None
        self.currentDatFile = None
        self.patternDumper = PatternDumper()
        self.patternDumper.printInfoCallback = self.msg.showInfo
        self.gui = Gui()
        self.gui.initializeMainWindow(self)
        self.patternListBox.bind('<<ListboxSelect>>', self.patternSelected)
        self.after_idle(self.canvasConfigured)
        self.deviceEntry.entryText.set(self.getConfig().device)
        self.datFileEntry.entryText.set(self.getConfig().datFile)
        self.initEmulator()
        self.after_idle(self.reloadPatternFile)
        
    def initEmulator(self):
        self.emu = PDDemulator(self.getConfig().imgdir)
        self.emu.listeners.append(PDDListener(self))
        self.setEmulatorStarted(False)
    
    def emuButtonClicked(self):
        self.getConfig().device = self.deviceEntry.entryText.get()
        if self.emu.started:
            self.stopEmulator()
        else:
            self.startEmulator()
        
    def startEmulator(self):
        self.msg.showInfo('Preparing emulator. . . Please Wait')

        if self.getConfig().simulateEmulator:
            self.msg.showInfo('Simulating emulator, emulator is not started...')
            self.setEmulatorStarted(True)
        else:
            try:
                port = self.getConfig().device
                self.emu.open(cport=port)
                self.msg.showInfo('PDDemulate Version 1.1 Ready!')
                self.setEmulatorStarted(True)
                self.after_idle(self.emulatorLoop)
            except Exception, e:
                self.msg.showError('Ensure that TFDI cable is connected to port ' + port + '\n\nError: ' + str(e))
                self.setEmulatorStarted(False)
        
    def emulatorLoop(self):
        if self.emu.started:
            self.emu.handleRequest()
            self.after_idle(self.emulatorLoop)
        
    def stopEmulator(self):
        if self.emu is not None:
            self.emu.close()
            self.msg.showInfo('PDDemulate stopped.')
            self.setEmulatorStarted(False)
        self.initEmulator()
        
    def quitApplication(self):
        self.stopEmulator()
        self.after_idle(self.quit)
        
    def setEmulatorStarted(self, started):
        self.emu.started = started
        if started:
            self.gui.setEmuButtonStarted()
        else:
            self.gui.setEmuButtonStopped()
    
    def getConfig(self):
        cfg = self._cfg
        if cfg is None:
            self._cfg = cfg = Config()
            if not hasattr(cfg, "device"):
                cfg.device = u""
            if not hasattr(cfg, "datFile"):
                cfg.datFile = u""
            if not hasattr(cfg, "simulateEmulator"):
                cfg.simulateEmulator = False
        return cfg
        
    def reloadPatternFile(self, pathToFile = None):
        if not pathToFile:
            pathToFile = self.datFileEntry.entryText.get()
        if not pathToFile:
            return
        self.currentDatFile = pathToFile
        try:
            result = self.patternDumper.dumppattern([pathToFile])
            self.patterns = result.patterns
            listBoxModel = []
            for p in self.patterns:
                listBoxModel.append(self.getPatternTitle(p))
            self.patternListBox.items.set(listBoxModel)
            if (len(listBoxModel) > 0):
                selected_index = 0
                self.patternListBox.selection_set(selected_index)
                self.displayPattern(self.patterns[selected_index])
            else:
                self.displayPattern(None)
        except IOError as e:
            self.msg.showError('Could not open pattern file %s' % pathToFile + '\n' + str(e))
        
    def reloadDatFileButtonClicked(self):
        self.reloadPatternFile()
        
    def patternSelected(self, evt):
        w = evt.widget
        sel = w.curselection()
        if len(sel) > 0:
            index = int(w.curselection()[0])
            pattern = self.patterns[index]
        else:
            pattern = None
        self.displayPattern(pattern)
        
    def displayPattern(self, pattern=None):
        if not pattern:
            pattern = self.pattern
        self.patternCanvas.clear()
        self.patternTitle.caption.set(self.getPatternTitle(pattern))
        if pattern:
            result = self.patternDumper.dumppattern([self.currentDatFile, str(pattern['number'])])
            self.printPatternOnCanvas(result.pattern)
        self.pattern = pattern
        
    def getPatternTitle(self, pattern):
        p = pattern
        if p:
            return 'Pattern no: ' + str(p['number']) + " (rows x stitches: " + str(p["rows"]) + " x " + str(p["stitches"]) + ")" 
        else:
            return 'No pattern'
    
    def printPatternOnCanvas(self, pattern):
        patternWidth = len(pattern)
        patternHeight = len(pattern[0])
        bitWidth = self.patternCanvas.getWidth() / patternWidth;
        bitHeight = self.patternCanvas.getHeight() / patternHeight;
        self.patternCanvas.clear()
        for row in range(len(pattern)):
            for stitch in range(len(pattern[row])):
                if(pattern[row][stitch]) == 0:
                    self.patternCanvas.create_rectangle(stitch * bitWidth,row * bitHeight,(stitch+1) * bitWidth,(row+1) * bitHeight, width=0, fill='black')
                    
    def canvasConfigured(self):
        self.msg.displayMessages = False
        self.displayPattern()
        self.msg.displayMessages = True
        self.after(100, self.canvasConfigured)

class PDDListener(PDDEmulatorListener):

    def __init__(self, app):
        self.app = app

    def dataReceived(self, fullFilePath):
        self.app.datFileEntry.entryText.set(fullFilePath)
        self.reloadPatternFile(fullFilePath)
    
    
if __name__ == "__main__":
    app = KnittingApp()
    app.mainloop()