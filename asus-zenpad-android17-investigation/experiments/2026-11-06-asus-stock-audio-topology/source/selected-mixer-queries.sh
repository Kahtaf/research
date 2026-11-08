[ "$(id -u)" = 0 ]
[ "$(getprop ro.product.device)" = P00A_2 ]
[ "$(getprop sys.boot_completed)" = 1 ]
for asus_mixer_name in Audio_MIC1_Mode_Select Audio_MicSource1_Setting Audio_Preamp1_Switch Audio_ADC_1_Switch Audio_Speaker_class_Switch Speaker_Amp_Switch Ext_Speaker_Amp_Switch; do
    printf 'ASUS_MIXER_QUERY=%s\n' "$asus_mixer_name"
    /system/bin/tinymix "$asus_mixer_name"
done
