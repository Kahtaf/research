#!/usr/bin/env python3
from source_edits import replace
replace('drivers/misc/mediatek/usb20/musb_gadget_ep0.c','\t\t\t\t\t\tDBG(0,\n\t\t\t\t\t\t\t"restarting the request\\n");\n\t\t\t\t\t\tmusb_ep_restart(musb, request);','\t\t\t\t\t\tDBG(0,\n\t\t\t\t\t\t\t"restarting the request\\n");\n\t\t\t\t\tmusb_ep_restart(musb, request);')
