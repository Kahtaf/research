# Source this file on the VM; these functions do nothing until called with
# actual externally reviewed inputs. No R9 profile or placeholder hash is created.
_v5_capture=/srv/android/asus-official-runtime-capture/preparation-v5/source/capture.py
v5_plan() {
  test "$#" -eq 2 || return 2
  python3 -B "$_v5_capture" plan --profile "$1" --profile-sha256 "$2"
}
v5_select() {
  test "$#" -eq 3 || return 2
  python3 -B "$_v5_capture" select --profile "$1" --profile-sha256 "$2" --name "$3"
}
v5_verify() {
  test "$#" -eq 5 || return 2
  python3 -B "$_v5_capture" verify --profile "$1" --profile-sha256 "$2" --name "$3" --selection "$4" --selection-sha256 "$5"
}
v5_copy() {
  test "$#" -eq 5 || return 2
  python3 -B "$_v5_capture" copy --mode PARENT_EXECUTE --profile "$1" --profile-sha256 "$2" --name "$3" --selection "$4" --selection-sha256 "$5"
}
