function isTrue(value) {
  if (value == true) return true;
  return false;
}  

function convertFromMillis(time) {
    time = time / 1000;
    var realTime = "";

    if (time >= 3600) {
        var hour = Math.floor(time / 3600);
        time = time - hour * 3600;
        realTime = hour + "h ";
    } else if (time >= 60) {
        var minute = Math.floor(time / 60);
        time = time - minute * 60;
        realTime = minute + "m ";
    } else {
        realTime = time + "s ";
    }

    return realTime;
}

function incValue(value) {
    return value + 1;
}

module.exports = {
    isTrue: isTrue,
    convertFromMillis: convertFromMillis,
    incValue: incValue
}