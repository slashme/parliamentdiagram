"use strict";

/**
 * similar to the python sum builtin
 * @param {Iterable<number>} ar
 * @param {number} start
 * @return {number}
 */
export function sum(ar, start = 0) {
    return (Array.isArray(ar) ? ar : [...ar])
        .reduce((a, b) => a + b, start);
}

// similar to functools.cache in python
export function cached(f) {
    const cache = new Map();
    return function (...args) {
        const key = JSON.stringify(args);
        if (!cache.has(key)) {
            cache.set(key, f(...args));
        }
        return cache.get(key);
    }
}

/**
 * similar to the python sorted builtin
 * @param {Iterable<T>} array
 * @param {Function} key
 * @param {boolean} reverse
 * @return {T[]}
 */
export function sorted(array, key = null, reverse = false) {
    return [...array].sort((a, b) => {
        if (key) {
            a = key(a);
            b = key(b);
        }
        let rv = 0;
        if (a < b) {
            rv = -1;
        } else if (a > b) {
            rv = 1;
        }
        if (reverse) {
            rv *= -1;
        }
        return rv;
    });
}
