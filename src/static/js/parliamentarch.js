"use strict";

/**
 * See the Python Parliamentarch module for documentation.
 * https://github.com/Gouvernathor/parliamentarch
 */

import { sorted, sum } from "parliamentarch/_util.js";
import { get_seats_centers, get_row_thickness, get_nrows_from_nseats } from "parliamentarch/geometry.js";
import { dispatch_seats, get_grouped_svg, SeatData } from "parliamentarch/svg.js";

// export * as geometry from "parliamentarch/geometry.js";
// export * as svg from "parliamentarch/svg.js";
export { SeatData } from "parliamentarch/svg.js";

/**
 * @param {Map<SeatData, number>} attrib
 * @param {number} seat_radius_factor
 * @param {Object} get_seats_centers_options
 * @param {Object} get_grouped_svg_options
 * @return {Element}
 */
export function get_svg_from_attribution(
    attrib,
    seat_radius_factor = .8,
    get_seats_centers_options = {},
    get_grouped_svg_options = {},
) {

    const nseats = sum(attrib.values());

    const results = get_seats_centers(nseats, get_seats_centers_options);
    // const sorted_coordinates = [...results.entries()].sort((a, b) => a[1] - b[1]).reverse().map(([k, v]) => k);
    const seat_centers_by_group = dispatch_seats(attrib, sorted(results.keys(), (a) => results.get(a), true));
    const seat_actual_radius = seat_radius_factor * get_row_thickness(get_nrows_from_nseats(nseats));
    return get_grouped_svg(seat_centers_by_group, seat_actual_radius, get_grouped_svg_options);
}
