
/**
 * @fileoverview A collection of utility functions.
 */

/**
 * Simple compare function.
 * @param {Object} a The first object to compare.
 * @param {number} a.x Sub element x to compare.
 * @param {Object} b The second object to compare.
 * @param {number} b.x Sub element x to compare.
 * @returns {number} 0 if equal, 1 if a.x > b.x, -1 if a.x < b.x.
 */
function compareX(a, b) {
    if (a.x < b.x)
        return -1;
    if (a.x > b.x)
        return 1;
    return 0;
}


/**
 * Get a random integer between min and max.
 * @param {number} min The minimum number.
 * @param {number} max The maximum number.
 * @return {number} A number between min and max.
 */
function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}


/**
 * Permutate arrays.
 * Example:
 *     let p = permutateArrays(['1', '2', '3'], ['A', 'B']]);
 *     console.log(p);
 *     [['1', 'A'], ['1', 'B'],
 *      ['2', 'A'], ['2', 'B'],
 *      ['3', 'A'], ['3', 'B']]
 *
 * Adapted from:
 * https://stackoverflow.com/questions/15298912/javascript-generating-combinations-from-n-arrays-with-m-elements
 *
 * @param arraysToCombine {Array} - array of arrays
 * @returns {Array} permutated array
 */
function permutateArrays(arraysToCombine) {
    let divisors = [];
    for (let i = arraysToCombine.length - 1; i >= 0; i--) {
        divisors[i] = divisors[i + 1]
            ? divisors[i + 1] * arraysToCombine[i + 1].length
            : 1;
    }

    function getPermutation(n, arraysToCombine) {
        let result = [];
        let curArray;
        for (let i = 0; i < arraysToCombine.length; i++) {
            curArray = arraysToCombine[i];
            result.push(
                curArray[Math.floor(n / divisors[i]) % curArray.length]
            );
        }
        return result;
    }

    let numPerms = arraysToCombine[0].length;
    for (let i = 1; i < arraysToCombine.length; i++) {
        numPerms *= arraysToCombine[i].length;
    }

    let combinations = [];
    for (let i = 0; i < numPerms; i++) {
        combinations.push(getPermutation(i, arraysToCombine));
    }

    return combinations;
}


/**
 * Convert bytes into highest unit.
 * @param x {number} Array of numbers.
 * @returns {string} The converted bytes into the highest unit.
 */
function niceBytes(x){
    let units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    let l = 0;
    let n = parseInt(x, 10) || 0;

    while(n >= 1024 && ++l){
        n = n/1024;
    }

  return(n.toFixed(n < 10 && l > 0 ? 1 : 0) + ' ' + units[l]);
}


/**
 * Get the mean of an array of numbers.
 * @param data {Array[number]} Array of numbers.
 * @returns {number} The mean of data.
 */
function mean(data) {
    let len = data.length;
    let sum = 0;
    for (let i = 0; i < len; i++) {
        sum += parseFloat(data[i]);
    }
    return (sum / len);
}


/**
 * Because .sort() doesn't sort numbers correctly
 * @param a {number} The 1st number to compare.
 * @param b {number} The 2nd number to compare.
 * @returns {number} -1, 0, 1.
 */
function numSort(a, b) {
    return a - b;
}


/**
 * Get any percentile from an array.
 * @param data {Array} - array of numbers
 * @param percentile {number} - which percentile to get
 * @returns {number} the "percentile" of "data"
 */
function getPercentile(data, percentile) {
    data.sort(numSort);
    let index = (percentile/100) * data.length;
    let result;
    if (Math.floor(index) === index) {
         result = (data[(index-1)] + data[index])/2;
    }
    else {
        result = data[Math.floor(index)];
    }
    return result;
}


/**
 * Wrap the percentile calls in one method.
 * @param data {Array} - array of numbers
 * @returns {{low: number, q1: number, median: number, q3: number, high: number}}
 */
function getBoxValues(data) {
    let filteredData = [];

    $.each(data, function(idx, elem) {
        if (!isNaN(elem)) {
            filteredData.push(elem);
        }
    });

    return {low: Math.min.apply(Math, filteredData),
            q1: getPercentile(filteredData, 25),
            median: getPercentile(filteredData, 50),
            q3: getPercentile(filteredData, 75),
            high: Math.max.apply(Math, filteredData)};
}


/**************************************************************************
 **
 ** LAYOUT ALGORITHMS
 **
 *************************************************************************/


function createShelf(width) {
    return {
        width: width,
        free: width,
        used: 0,
        elements: []
    }
}

function addItems(shelves, items, width) {

    if (shelves.length === 0) {
        shelves.push(createShelf(width));
    }

    let spacing = 1000;
    //items.sort(function(a, b) {
    //    return (a.position_start - b.position_start);
    //});

    items.sort(function(a, b) {
        return (b.position_end - b.position_start) - (a.position_end - a.position_start);
    });

    //console.log('ADD ITEMS');
    $.each(items, function(i, item) {
        //console.log('ITEM=', item.name, item.position_end - item.position_start)
        let shelved = false;
        $.each(shelves, function(x, shelf) {

            if (shelf.elements.length === 0) {
                shelf.elements.push(item);
                shelf.free -= (item.end - item.start);
                shelf.used += (item.end - item.start);
                shelved = true;
                // break out of loop, go to next item
                return false;
            }

            // is there enough room?
            if (shelf.free > (item.end - item.start)) {
                // there is room, but can it fit in available slots?
                let canFit = true;
                $.each(shelf.elements, function(y, element) {
                    if (((item.start - spacing <= element.start) && (item.end + spacing >= element.start)) ||
                        ((item.start - spacing >= element.start) && (item.start - spacing <= element.end))) {
                        canFit = false;
                        // break out of loop
                        return false;
                    }
                });

                if (canFit) {
                    shelf.elements.push(item);
                    shelf.free -= (item.end - item.start);
                    shelf.used += (item.end - item.start);
                    shelved = true;
                }

                if (shelved) {
                    // break out of loop
                    return false;
                }
            }

        });
        if (!shelved) {
            let shelf = createShelf(width);
            shelf.elements.push(item);
            shelf.free -= (item.end - item.start);
            shelf.used += (item.end - item.start);
            shelves.push(shelf);
        }
    });


    return shelves;
}


///////////////////




function calculateTickIncrement(start, stop, count) {
var e10 = Math.sqrt(50),
    e5 = Math.sqrt(10),
    e2 = Math.sqrt(2);
  var step = (stop - start) / Math.max(0, count),
      power = Math.floor(Math.log(step) / Math.LN10),
      error = step / Math.pow(10, power);
  return power >= 0
      ? (error >= e10 ? 10 : error >= e5 ? 5 : error >= e2 ? 2 : 1) * Math.pow(10, power)
      : -Math.pow(10, -power) / (error >= e10 ? 10 : error >= e5 ? 5 : error >= e2 ? 2 : 1);
}

function calculateTicks(start, stop, count) {
  var reverse,
      i = -1,
      n,
      ticks,
      step;

  stop = +stop, start = +start, count = +count;
  if (start === stop && count > 0) return [start];
  if (reverse = stop < start) n = start, start = stop, stop = n;
  if ((step = calculateTickIncrement(start, stop, count)) === 0 || !isFinite(step)) return [];

  if (step > 0) {
    let r0 = Math.round(start / step), r1 = Math.round(stop / step);
    if (r0 * step < start) ++r0;
    if (r1 * step > stop) --r1;
    ticks = new Array(n = r1 - r0 + 1);
    while (++i < n) ticks[i] = (r0 + i) * step;
  } else {
    step = -step;
    let r0 = Math.round(start * step), r1 = Math.round(stop * step);
    if (r0 / step < start) ++r0;
    if (r1 / step > stop) --r1;
    ticks = new Array(n = r1 - r0 + 1);
    while (++i < n) ticks[i] = (r0 + i) / step;
  }

  if (reverse) ticks.reverse();

  return ticks;
}


/////////
const BASES_LIST = ['A','C','G','T'];
const BASES_DICT = {'A': '0', 'C': '1', 'G': '2', 'T': '3'};
const CC = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

function numberToBase(n, b) {
    if (n === 0)
        return [0]
    let digits = [];
    while (n) {
        digits.push(Math.round(n % b))
        n = Math.floor(n / b)
    }
    return digits.reverse().join('')
}

function sdpn_to_sdpN(sdpn, fill=-1) {
    return numberToBase(sdpn, 4).padStart(8, '0');
}
function sdpN_to_sdpn(sdpN) {
    return parseInt(""+sdpN, 4)
}
function sdpn_to_sdpB(sdpn) {
    let spdN = sdpn_to_sdpN(sdpn);
    let B = [];
    for (let x = 0; x < spdN.length; x++) {
        B.push(BASES_LIST[parseInt(spdN[x])]);
    }
    return B;
}
function sdpn_to_sdpD(sdpn, sort=null) {
    let l = {};
    let sdpB = sdpn_to_sdpB(sdpn);

    for (let x = 0; x < sdpB.length; x++) {
        if (sdpB[x] in l) {
            l[sdpB[x]] = l[sdpB[x]] + CC[x];
        } else {
            l[sdpB[x]] = CC[x];
        }
    }

    let n = [];

    if (sort != null) {
        for (let b in sort) {
            if (sort[b] in l) {
                n.push(l[sort[b]]);
            }
        }
    } else {
        let temp = [];
        for (const [key, value] of Object.entries(l)) {
            temp.push({'base': key, 'num': value.length});
        }
        temp = temp.sort(function(a, b) {
            return (a.num > b.num) ? 1 : -1;

        }).reverse();

        for (let x = 0; x < temp.length; x++) {
            n.push(l[temp[x].base]);
        }

    }

    return n.join(':');
}
