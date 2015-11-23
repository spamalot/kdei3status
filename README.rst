
KDE Plasma 4 applet that displays the output of i3status.

When the mouse hovers over the widget, or the active window is
changed, the title of the active window will be displayed.

To build and install the plasmoid, from the directory level above the
hierarchy kdei3status/contents/code/main.py, run::

    $ plasmapkg -r kdei3status  # Uninstall if already installed.
    $ plasmapkg -i kdei3status  # Install from the directory.
    $ kbuildsycoca4  # Rebuild config cache.

To test the plasmoid, run::

    $ plasmoidviewer kdei3status


Changing Formatting
+++++++++++++++++++

Formatting and colors are obtained by a mix of HTML and patching the
i3status formatting output. The current implementation therefore
requires that i3status have an output format of xmobar, and that HTML
patching be applied in the ``reloadI3statusText`` method of the
applet.
