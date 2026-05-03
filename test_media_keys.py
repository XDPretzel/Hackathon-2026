import AppKit
import Quartz

def HIDPostAuxKey(key):
    NX_SYSDEFINED = 14
    def doKey(down):
        ev = AppKit.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
            NX_SYSDEFINED, # type
            (0, 0),        # location
            0xa00 if down else 0xb00, # modifierFlags
            0,             # timestamp
            0,             # windowNumber
            None,          # context
            8,             # subtype
            (key << 16) | ((0xa if down else 0xb) << 8), # data1
            -1             # data2
        )
        Quartz.CGEventPost(0, ev.CGEvent())

    doKey(True)
    doKey(False)

# 16 is Play/Pause
HIDPostAuxKey(16)
