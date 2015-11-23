# This file is part of kdei3status
#
# kdei3status is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kdei3status is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kdei3status.  If not, see <http://www.gnu.org/licenses/>.

"""KDE Plasma 4 applet that displays the output of i3status.

When the mouse hovers over the widget, or the active window is
changed, the title of the active window will be displayed.

Formatting and colors are obtained by a mix of HTML and patching the
i3status formatting output. The current implementation therefore
requires that i3status have an output format of xmobar, and that HTML
patching be applied in the ``reloadI3statusText`` method of the
applet.

To build and install the plasmoid, from the directory level above the
hierarchy kdei3status/contents/code/main.py, run:

    $ plasmapkg -r kdei3status  # Uninstall if already installed.
    $ plasmapkg -i kdei3status  # Install from the directory.
    $ kbuildsycoca4  # Rebuild config cache.

To test the plasmoid, run:

    $ plasmoidviewer kdei3status

"""

# NOTE: camelCase is used throughout this script for consistency with
# the Qt naming scheme.

import subprocess
import re

from PyQt4.QtCore import QTimer, Qt
from PyQt4.QtGui import QGraphicsLinearLayout, QSizePolicy, QIcon
from PyKDE4 import plasmascript
from PyKDE4.plasma import Plasma
from PyKDE4.kdeui import KWindowSystem, NET


# Should match the refresh interval of the i3status configuration.
I3STATUS_REFRESH_INTERVAL = 1000

# How long to display a new window title when the active window
# changes.
TITLE_DISPLAY_TIMEOUT = 1000


def execute(command):
    """Run a command line program and yield its lines of output."""
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines = iter(popen.stdout.readline, b"")
    for line in lines:
        yield line


class MainApplet(plasmascript.Applet):
    def __init__(self, parent, args=None):
        plasmascript.Applet.__init__(self, parent)

        # Currently active window ID. None if no window is active.
        self.wid = None

        self.titleTextShown = False
        self.hovered = False
        self.i3statusText = ''
        self.titleText = ''

    def init(self):
        # Fill space if in a horizontal panel.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                        QSizePolicy.Preferred))

        layout = QGraphicsLinearLayout(Qt.Horizontal, self.applet)
        layout.setContentsMargins(0, 0, 0, 0)
        self.applet.setLayout(layout)

        self.icon = Plasma.IconWidget(self.applet)
        self.label = Plasma.Label(self.applet)
        # TODO: Improve handling of very long window titles.
        self.label.setWordWrap(False)

        layout.addItem(self.icon)
        layout.addItem(self.label)
        layout.setStretchFactor(self.label, 1)

        # Reasonable default size -- can be resized later by user.
        self.resize(500, 30)

        self.refreshTimer = QTimer()
        self.refreshTimer.setInterval(I3STATUS_REFRESH_INTERVAL)
        self.refreshTimer.timeout.connect(self.reloadI3statusText)
        self.statusIterator = execute(["i3status"])
        self.refreshTimer.start()

        self.windowChangeTimer = QTimer()
        self.windowChangeTimer.setSingleShot(True)
        self.windowChangeTimer.setInterval(TITLE_DISPLAY_TIMEOUT)
        self.windowChangeTimer.timeout.connect(self.hideTitleText)

        KWindowSystem.self().windowRemoved.connect(self.windowRemoved)
        KWindowSystem.self().windowChanged.connect(self.windowChanged)
        KWindowSystem.self().activeWindowChanged.connect(
            self.activeWindowChanged)

    def windowChanged(self, wid, props):
        if wid == self.wid and props & NET.WMName:
            self.reloadTitleText()
            if self.titleTextShown:
                self.showTitleText()

    def windowRemoved(self, wid):
        if wid == self.wid:
            self.wid = None

    def activeWindowChanged(self, wid):
        self.wid = wid
        self.reloadTitleText()
        self.showTitleText()
        self.windowChangeTimer.start()
        self.icon.setIcon(QIcon(KWindowSystem.icon(wid)))

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.showTitleText()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.hideTitleText()

    def showTitleText(self):
        """Show the title text of the active window."""
        self.titleTextShown = True
        self.label.setText(self.titleText)

    def hideTitleText(self):
        """Hide the title text of the active window so that the
        i3status text is shown.

        Does nothing if hovered by the mouse.

        """
        if self.hovered:
            return
        self.titleTextShown = False
        self.label.setText(self.i3statusText)

    def reloadTitleText(self):
        """Get the window title from the active window."""
        windowInfo = KWindowSystem.windowInfo(self.wid, NET.WMName)
        self.titleText = windowInfo.name()

    def reloadI3statusText(self):
        """Get the next output from i3status and display it if a
        window title is not shown.

        """
        try:
            text = next(self.statusIterator)
        except StopIteration:
            print('i3status was killed; respawning...')
            self.statusIterator = execute(["i3status"])
            self.reloadText()
            return
        # This is where all the formatting patching occurs.
        # Change along with the i3status config file to suit your
        # formatting preferences
        self.i3statusText = re.sub(
            'fc=(.+?)>', r'span style="color:\1">', text).replace(
                '/fc', '/span').replace(
                '(<small>remaining</small>)', '')
        if self.titleTextShown:
            return
        self.label.setText(self.i3statusText)


def CreateApplet(parent):
    return MainApplet(parent)
