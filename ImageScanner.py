#!/usr/bin/env python
# -*- coding: utf8 -*-

import pygtk
pygtk.require20()
import gtk
import gobject

from datetime import datetime
import os.path

import imagescanner
from imagescanner.backends.twain import twain as _twain

# imagescanner setup
imagescanner.settings.ENABLE_NET_BACKEND = False
imagescanner.settings.ENABLE_TEST_BACKEND = False

# replace base twain backend
imagescanner.core._imagescanner.NT_BACKEND = 'TwainDecorator'

class ImageScanner(object):
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file('Resources/MainWindow.glade')

        signals = { 'on_scanBtn_clicked' : self.on_scanBtn_clicked,
                    'on_loadBtn_clicked' : self.on_loadBtn_clicked }
        builder.connect_signals(signals)

        self.main_window = builder.get_object('mainWindow')
        self.main_window.connect('destroy', gtk.main_quit)
        
        self.scanner_combo = builder.get_object('scannerCombo')
        self.target_dir_btn = builder.get_object('targetDirBtn')
        self.dpi_combo = builder.get_object('dpiCombo')
        self.format_combo = builder.get_object('formatCombo')
        
        self.scanners = {}
        
        self.main_window.show_all()
    
    def main(self):
        try:
            gtk.main()
        except BaseException as e:
            # uklid
            raise
    
    def on_scanBtn_clicked(self, widget, data = None):
        try:
            self.main_window.set_sensitive(False)

            scanner_name = self.__get_active_item(self.scanner_combo)
            if scanner_name == None:
                self.__show_error('Vyberte skener z nabídky.')
                return
            scanner = self.scanners[scanner_name]
            
            dpi = self.__get_active_item(self.dpi_combo)
            form = self.__get_active_item(self.format_combo)
            
            target_dir = self.target_dir_btn.get_current_folder()
            if target_dir == None:
                self.__show_error('Vyberte cílový adresář.')
                return
            
            image = self.__scan_image(scanner, dpi)
            self.__store_image(target_dir, image, form)
        finally:
            self.main_window.set_sensitive(True)
    
    def on_loadBtn_clicked(self, widget, data = None):
        try:
            self.main_window.set_sensitive(False)

            try:
                self.__load_scanners()
            except Exception as e:
                self.__show_error('Chyba při načítání dostupných skenerů:\n\n' + str(e))
            
            self.__set_scanners_to_model()
        finally:
            self.main_window.set_sensitive(True)
    
    def __load_scanners(self):
        iscan = imagescanner.ImageScanner()
        scanners = iscan.list_scanners()
        for scanner in scanners:
            if scanner.name not in self.scanners:
                self.scanners[scanner.name] = scanner
            else:
                self.scanners[scanner.id] = scanner
    
    def __set_scanners_to_model(self):
        if len(self.scanners) == 0:
            return
        model = self.scanner_combo.get_model()
        for scanner_name in self.scanners.keys():
            model.append([scanner_name])
    
    def __show_error(self, message):
        dialog = gtk.MessageDialog(parent=self.main_window, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=message)
        dialog.run()
        dialog.destroy()
    
    def __get_active_item(self, combo):
        model = combo.get_model()
        active = combo.get_active()
        if (active < 0):
            return None
        return model[active][0]
    
    def __scan_image(self, scanner, dpi):
        self.__set_scanner_settings(scanner, dpi)
        image = scanner.scan(dpi)
        self.__remove_scanner_settings(scanner)
        return image

    def __set_scanner_settings(self, scanner, dpi):
        rgbCap = lambda scanner: scanner.SetCapability( \
                       _twain.ICAP_PIXELTYPE, \
                       _twain.TWTY_UINT16, \
                       _twain.TWPT_RGB)
##        dpiXCap = lambda scanner: scanner.SetCapability( \
##                       _twain.ICAP_XRESOLUTION, \
##                       _twain.TWTY_FIX32, \
##                       float(dpi))
##        dpiYCap = lambda scanner: scanner.SetCapability( \
##                       _twain.ICAP_YRESOLUTION, \
##                       _twain.TWTY_FIX32, \
##                       float(dpi))
        
        scanner._scan_before_event.append(rgbCap)
##        scanner._scan_before_event.append(dpiXCap)
##        scanner._scan_before_event.append(dpiYCap)

    def __remove_scanner_settings(self, scanner):
        scanner._scan_before_event = scanner._scan_before_event[:-3]
    
    def __store_image(self, target_dir, image, img_format):
        path = self.__build_path(target_dir, img_format)
        while os.path.exists(path):
            path = self.__build_path(target_dir, img_format)
        image.save(path, img_format)

    def __build_path(self, target_dir, img_format):
        now = datetime.now()
        filename = 'Scanned_at_%s.%s' % (now.strftime('%Y-%m-%d_%H-%M-%S'), img_format.lower())
        return os.path.join(target_dir, filename)

if __name__ == '__main__':
    gui = ImageScanner()
    gui.main()
