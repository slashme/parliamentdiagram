"use strict";

import { sum } from "parliamentarch/_util.js";

export class SeatData {
    /**
     * @param {string} data
     * @param {string} color
     * @param {number} border_size
     * @param {string} border_color
     */
    constructor(data, color, border_size = 0, border_color = "#000") {
        this.id = null;
        this.data = data;
        this.color = color;
        this.border_size = border_size;
        this.border_color = border_color;
    }

    get sanitized_data() {
        return this.data.replace(/[^a-zA-Z0-9_-]/g, "-");
    }
}

/**
 * @param {Map<SeatData, number>} group_seats
 * @param {Iterable<S>} seats
 * @return {Map<SeatData, S[]>}
 */
export function dispatch_seats(group_seats, seats) {
    const seatIterator = seats[Symbol.iterator]();
    const rv = new Map();
    for (const [group, nseats] of group_seats.entries()) {
        const group_seats = [];
        for (let i = 0; i < nseats; i++) {
            const seat = seatIterator.next();
            if (seat.done) {
                throw new Error("Not enough seats");
            }
            group_seats.push(seat.value);
        }
        rv.set(group, group_seats);
    }
    if (!seatIterator.next().done) {
        throw new Error("Too many seats");
    }
    return rv;
}

/**
 * @param {Map<[number, number], SeatData>} seat_centers
 * @param  {...any} args
 * @return {Element}
 */
export function get_svg(seat_centers, ...args) {
    const seat_centers_by_group = new Map();
    for (const [seat, group] of seat_centers.entries()) {
        if (!seat_centers_by_group.has(group)) {
            seat_centers_by_group.set(group, []);
        }
        seat_centers_by_group.get(group).push(seat);
    }
    return get_grouped_svg(seat_centers_by_group, ...args);
}

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

/**
 * @param {Map<SeatData, [number, number][]>} seat_centers_by_group
 * @param {number} seat_actual_radius
 * @param {Object} options
 * @param {number} [options.canvas_size]
 * @param {number|[number, number]|[number, number, number, number]} [options.margins]
 * @param {boolean} [options.write_number_of_seats]
 * @param {number} [options.font_size_factor]
 * @return {Element}
 */
export function get_grouped_svg(
    seat_centers_by_group,
    seat_actual_radius,
    {
        canvas_size = 175,
        margins = 5.,
        write_number_of_seats = true,
        font_size_factor = 36 / 175,
    } = {}) {

    if (!Array.isArray(margins)) {
        margins = [margins, margins, margins, margins];
    } else if (margins.length === 2) {
        margins = [margins[0], margins[1], margins[0], margins[1]];
    }
    const [left_margin, top_margin, right_margin, bottom_margin] = margins;

    const svg = document.createElementNS(SVG_NAMESPACE, "svg");

    populate_header(svg,
        left_margin + 2 * canvas_size + right_margin,
        top_margin + canvas_size + bottom_margin);
    if (write_number_of_seats) {
        add_number_of_seats(svg,
            sum(Array.from(seat_centers_by_group.values(), group => group.length)),
            left_margin + canvas_size,
            top_margin + (canvas_size * 170 / 175),
            Math.round(font_size_factor * canvas_size));
    }
    add_grouped_seats(svg, seat_centers_by_group, seat_actual_radius,
        canvas_size, left_margin, top_margin);

    return svg
}

/**
 * @param {Element} svg
 * @param {number} width
 * @param {number} height
 */
function populate_header(svg, width, height) {
    svg.setAttribute("xmlns", SVG_NAMESPACE);
    svg.setAttribute("version", "1.1");
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
}

/**
 * @param {Element} svg
 * @param {number} nseats
 * @param {number} x
 * @param {number} y
 * @param {number} font_size
 */
function add_number_of_seats(svg, nseats, x, y, font_size) {
    const text = svg.appendChild(document.createElementNS(SVG_NAMESPACE, "text"));
    text.setAttribute("x", x);
    text.setAttribute("y", y);
    text.setAttribute("style", `font-size: ${font_size}px; font-weight: bold; text-align: center; text-anchor: middle; font-family: sans-serif;`);
    text.textContent = nseats.toString();
}

/**
 * @param {Element} svg
 * @param {Map<SeatData, [number, number][]>} seat_centers_by_group
 * @param {number} seat_actual_radius
 * @param {number} canvas_size
 * @param {number} left_margin
 * @param {number} top_margin
 */
function add_grouped_seats(svg,
    seat_centers_by_group,
    seat_actual_radius,
    canvas_size,
    left_margin,
    top_margin,
) {

    let group_number_fallback = 0;

    for (const [group, seat_centers] of seat_centers_by_group.entries()) {
        let group_number = group.id;
        if (group_number === null) {
            group_number = group_number_fallback;
            group_number_fallback++;
        }

        const group_border_width = group.border_size * seat_actual_radius * canvas_size;

        const group_g = svg.appendChild(document.createElementNS(SVG_NAMESPACE, "g"));

        let g_style = `fill: ${group.color};`;
        if (group_border_width > 0) {
            g_style += ` stroke-width: ${group_border_width}; stroke: ${group.border_color};`;
        }
        group_g.setAttribute("style", g_style);

        group_g.setAttribute("id", `${group_number}-${group.sanitized_data}`);

        if (group.data && group.data !== "") {
            group_g.appendChild(document.createElementNS(SVG_NAMESPACE, "title")).textContent = group.data;
        }

        for (const [x, y] of seat_centers) {
            const circle = group_g.appendChild(document.createElementNS(SVG_NAMESPACE, "circle"));
            circle.setAttribute("cx", left_margin + canvas_size * x);
            circle.setAttribute("cy", top_margin + canvas_size * (1 - y));
            circle.setAttribute("r", seat_actual_radius * canvas_size - group_border_width / 2);
        }
    }
}
