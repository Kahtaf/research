# Stock legacy RAM USB reporter trial

Question: does the existing stock android_usb driver expose the read-only RAM report? Status: parent preflight, one recovery-only trial; no kernel or normal OS partition change. Outputs: evidence and private raw records. Continue after one boot with retained marker collection; no automatic retry after uncertain dispatch. Existing owner Power fallback authorization retained.

## Physical result

PASS for stock-specific USB RAM reporter: fresh exact descriptor ASUS-PID1:3.18.35 and serial appeared, correct FAT report read, host WritableMedia=false and WritableVolume=false independently captured, and new verified Android boot returned. Original observer used wrong diskutil boolean keys; its false readonly interpretation is corrected by separate raw-property receipt without another run. Normal OS partitions untouched. This is stock-specific and does not prove4.9. See evidence/physical-result.json.
