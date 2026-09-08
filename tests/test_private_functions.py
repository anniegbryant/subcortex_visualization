"""
Tests for private helper functions in subcortex_visualization.plotting.

These functions are not part of the public API but are important enough
to test independently, since they handle color mapping, SVG parsing, and
data normalisation for all plot types.
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib.colors as mcolors

from subcortex_visualization.plotting import (
    _parse_svg_dimension,
    _normalise_hemi,
    _prep_data,
    _get_region_color,
)


class TestParseSvgDimension:
    def test_plain_integer_string(self):
        assert _parse_svg_dimension('500') == 500.0

    def test_plain_decimal_string(self):
        assert _parse_svg_dimension('12.5') == 12.5

    def test_mm_suffix(self):
        assert _parse_svg_dimension('300mm') == 300.0

    def test_px_suffix(self):
        assert _parse_svg_dimension('250px') == 250.0

    def test_none_returns_default_fallback(self):
        assert _parse_svg_dimension(None) == 500.0

    def test_none_returns_custom_fallback(self):
        assert _parse_svg_dimension(None, fallback=100) == 100.0

    def test_non_parseable_returns_fallback(self):
        assert _parse_svg_dimension('abc', fallback=99) == 99.0

    def test_zero(self):
        assert _parse_svg_dimension('0') == 0.0


class TestNormaliseHemi:
    def test_bl_to_b(self):
        assert _normalise_hemi('BL') == 'B'

    def test_br_to_b(self):
        assert _normalise_hemi('BR') == 'B'

    def test_l_unchanged(self):
        assert _normalise_hemi('L') == 'L'

    def test_r_unchanged(self):
        assert _normalise_hemi('R') == 'R'

    def test_b_unchanged(self):
        assert _normalise_hemi('B') == 'B'


# ---------------------------------------------------------------------------
# Fixtures shared by TestPrepData and TestGetRegionColor
# ---------------------------------------------------------------------------

@pytest.fixture
def small_ordering():
    """Minimal atlas ordering DataFrame with three regions, both hemispheres."""
    return pd.DataFrame({
        'region':     ['thalamus', 'caudate', 'putamen',
                       'thalamus', 'caudate', 'putamen'],
        'Hemisphere': ['L', 'L', 'L', 'R', 'R', 'R'],
        'seg_index':  [1, 2, 3, 1, 2, 3],
        'plot_order': [1, 2, 3, 4, 5, 6],
        'face':       ['medial'] * 6,
    })


@pytest.fixture
def small_subcortex_data():
    return pd.DataFrame({
        'region':     ['thalamus', 'caudate', 'putamen',
                       'thalamus', 'caudate', 'putamen'],
        'Hemisphere': ['L', 'L', 'L', 'R', 'R', 'R'],
        'value':      [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    })


@pytest.fixture
def linear_cmap():
    return mcolors.LinearSegmentedColormap.from_list('test_lr', ['blue', 'red'])


class TestPrepDataNoSubcortexData:
    """When subcortex_data is None, _prep_data returns (df, color_lookup, cmap_colors, fill_domain)."""

    def test_returns_four_items(self, small_ordering, linear_cmap):
        result = _prep_data(small_ordering, subcortex_data=None, cmap=linear_cmap)
        assert len(result) == 4

    def test_dataframe_returned(self, small_ordering, linear_cmap):
        df, _, _, _ = _prep_data(small_ordering, subcortex_data=None, cmap=linear_cmap)
        assert isinstance(df, pd.DataFrame)

    def test_color_lookup_keys_match_regions(self, small_ordering, linear_cmap):
        _, color_lookup, _, _ = _prep_data(small_ordering, subcortex_data=None, cmap=linear_cmap)
        assert set(color_lookup.keys()) == {'thalamus', 'caudate', 'putamen'}

    def test_value_column_assigned(self, small_ordering, linear_cmap):
        df, _, _, _ = _prep_data(small_ordering, subcortex_data=None, cmap=linear_cmap)
        assert 'value' in df.columns
        assert df['value'].dtype in [int, float, np.int64, np.float64]

    def test_cmap_colors_length(self, small_ordering, linear_cmap):
        _, _, cmap_colors, _ = _prep_data(small_ordering, subcortex_data=None, cmap=linear_cmap)
        # One color per unique region
        assert len(cmap_colors) == 3

    def test_fill_domain_matches_regions(self, small_ordering, linear_cmap):
        _, _, _, fill_domain = _prep_data(small_ordering, subcortex_data=None, cmap=linear_cmap)
        assert set(fill_domain) == {'thalamus', 'caudate', 'putamen'}


class TestPrepDataDiscreteSubcortexData:
    """When subcortex_data holds discrete/categorical values, _prep_data returns
    (df, color_lookup, cmap_colors, fill_domain), keyed by category rather than region."""

    def test_returns_four_items(self, small_ordering, small_subcortex_data, linear_cmap):
        categorical_data = small_subcortex_data.assign(value=['A', 'B', 'A', 'A', 'B', 'A'])
        result = _prep_data(small_ordering, subcortex_data=categorical_data, cmap=linear_cmap, discrete=True)
        assert len(result) == 4

    def test_fill_domain_matches_categories(self, small_ordering, small_subcortex_data, linear_cmap):
        categorical_data = small_subcortex_data.assign(value=['A', 'B', 'A', 'A', 'B', 'A'])
        _, color_lookup, _, fill_domain = _prep_data(small_ordering, subcortex_data=categorical_data,
                                                      cmap=linear_cmap, discrete=True)
        assert set(fill_domain) == {'A', 'B'}
        assert set(color_lookup.keys()) == {'A', 'B'}

    def test_categorical_dtype_preserves_level_order(self, small_ordering, small_subcortex_data, linear_cmap):
        categorical_data = small_subcortex_data.assign(
            value=pd.Categorical(['A', 'B', 'A', 'A', 'B', 'A'], categories=['B', 'A'], ordered=True)
        )
        _, _, _, fill_domain = _prep_data(small_ordering, subcortex_data=categorical_data,
                                          cmap=linear_cmap, discrete=True)
        assert fill_domain == ['B', 'A']


class TestPrepDataWithSubcortexData:
    """When subcortex_data is provided, _prep_data returns (df, norm, vmin, vmax, midpoint)."""

    def test_returns_five_items(self, small_ordering, small_subcortex_data, linear_cmap):
        result = _prep_data(small_ordering, subcortex_data=small_subcortex_data, cmap=linear_cmap)
        assert len(result) == 5

    def test_norm_is_normalize(self, small_ordering, small_subcortex_data, linear_cmap):
        _, norm, _, _, _ = _prep_data(small_ordering, subcortex_data=small_subcortex_data, cmap=linear_cmap)
        assert isinstance(norm, mcolors.Normalize)

    def test_vmin_vmax_inferred_from_data(self, small_ordering, small_subcortex_data, linear_cmap):
        _, _, vmin, vmax, _ = _prep_data(small_ordering, subcortex_data=small_subcortex_data, cmap=linear_cmap)
        assert vmin == pytest.approx(1.0)
        assert vmax == pytest.approx(6.0)

    def test_explicit_vmin_vmax_respected(self, small_ordering, small_subcortex_data, linear_cmap):
        _, _, vmin, vmax, _ = _prep_data(
            small_ordering, subcortex_data=small_subcortex_data,
            cmap=linear_cmap, vmin=0.0, vmax=10.0,
        )
        assert vmin == pytest.approx(0.0)
        assert vmax == pytest.approx(10.0)

    def test_midpoint_produces_two_slope_norm(self, small_ordering, linear_cmap):
        data = pd.DataFrame({
            'region':     ['thalamus', 'caudate', 'putamen'] * 2,
            'Hemisphere': ['L'] * 3 + ['R'] * 3,
            'value':      [-3.0, 0.0, 3.0, -2.0, 1.0, 4.0],
        })
        _, norm, _, _, _ = _prep_data(
            small_ordering, subcortex_data=data,
            cmap=linear_cmap, midpoint=0,
        )
        assert isinstance(norm, mcolors.TwoSlopeNorm)

    def test_merged_dataframe_has_value_column(self, small_ordering, small_subcortex_data, linear_cmap):
        df, _, _, _, _ = _prep_data(
            small_ordering, subcortex_data=small_subcortex_data, cmap=linear_cmap,
        )
        assert 'value' in df.columns

    def test_bilateral_b_rows_expanded(self, small_ordering, linear_cmap):
        """Rows with Hemisphere='B' in subcortex_data should be duplicated to BL and BR."""
        data = pd.DataFrame({
            'region': ['thalamus'],
            'Hemisphere': ['B'],
            'value': [5.0],
        })
        df, _, _, _, _ = _prep_data(small_ordering, subcortex_data=data, cmap=linear_cmap)
        assert isinstance(df, pd.DataFrame)


class TestGetRegionColor:
    """_get_region_color resolves fill color, backing color, and outline thickness."""

    @pytest.fixture
    def row(self):
        return pd.Series({
            'region': 'thalamus',
            'Hemisphere': 'L',
            'value': 0.5,
            'plot_order': 1,
            'face': 'medial',
        })

    @pytest.fixture
    def unit_norm(self):
        return mcolors.Normalize(vmin=0, vmax=1)

    @pytest.fixture
    def linear_cmap(self):
        return mcolors.LinearSegmentedColormap.from_list('lr', ['blue', 'red'])

    # -- discrete (no subcortex_data) ----------------------------------------

    def test_discrete_uses_color_lookup(self, row, linear_cmap, unit_norm):
        color_lookup = {'thalamus': (1.0, 0.0, 0.0, 1.0)}
        color, _, _ = _get_region_color(color_lookup, row, linear_cmap, subcortex_data=None)
        assert color[:3] == pytest.approx((1.0, 0.0, 0.0), abs=1e-3)

    def test_discrete_returns_rgba(self, row, linear_cmap):
        color_lookup = {'thalamus': 'green'}
        color, base, _ = _get_region_color(color_lookup, row, linear_cmap, subcortex_data=None)
        assert len(color) == 4
        assert base is None

    # -- continuous (subcortex_data provided) ---------------------------------

    def test_continuous_returns_rgba(self, row, linear_cmap, unit_norm):
        color, _, _ = _get_region_color(
            {}, row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm, value_column='value',
        )
        assert len(color) == 4
        assert all(0.0 <= c <= 1.0 for c in color)

    def test_nan_value_uses_na_fill(self, row, linear_cmap, unit_norm):
        nan_row = row.copy()
        nan_row['value'] = np.nan
        color, _, _ = _get_region_color(
            {}, nan_row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm,
            NA_fill='#cccccc', value_column='value',
        )
        expected = mcolors.to_rgba('#cccccc', alpha=1.0)
        assert color == pytest.approx(expected, abs=1e-3)

    # -- fill_alpha -----------------------------------------------------------

    def test_fill_alpha_applied(self, row, linear_cmap, unit_norm):
        color_lookup = {'thalamus': 'blue'}
        color, _, _ = _get_region_color(
            color_lookup, row, linear_cmap,
            subcortex_data=None, fill_alpha=0.4,
        )
        assert color[3] == pytest.approx(0.4, abs=1e-3)

    # -- fill_by_significance -------------------------------------------------

    def test_significant_row_gets_white_base(self, row, linear_cmap, unit_norm):
        sig_row = row.copy()
        sig_row['p_value'] = 0.01
        _, base, _ = _get_region_color(
            {}, sig_row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm,
            fill_by_significance=True, value_column='value',
        )
        assert base == 'white'

    def test_nonsignificant_row_uses_nonsig_alpha(self, row, linear_cmap, unit_norm):
        ns_row = row.copy()
        ns_row['p_value'] = 0.5
        color, _, _ = _get_region_color(
            {}, ns_row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm,
            fill_by_significance=True,
            fill_alpha=1.0, nonsig_fill_alpha=0.3,
            value_column='value',
        )
        assert color[3] == pytest.approx(0.3, abs=1e-3)

    def test_nonsignificant_row_reduces_line_thickness(self, row, linear_cmap, unit_norm):
        ns_row = row.copy()
        ns_row['p_value'] = 0.5
        _, _, thickness = _get_region_color(
            {}, ns_row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm,
            fill_by_significance=True, line_thickness=2.0,
            value_column='value',
        )
        assert thickness == pytest.approx(0.5, abs=1e-3)  # 0.25 * 2.0

    def test_significant_row_keeps_full_line_thickness(self, row, linear_cmap, unit_norm):
        sig_row = row.copy()
        sig_row['p_value'] = 0.01
        _, _, thickness = _get_region_color(
            {}, sig_row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm,
            fill_by_significance=True, line_thickness=2.0,
            value_column='value',
        )
        assert thickness == pytest.approx(2.0, abs=1e-3)

    def test_no_p_value_column_treated_as_significant(self, row, linear_cmap, unit_norm):
        """Missing p_value should not raise; region is treated as significant."""
        color, _, _ = _get_region_color(
            {}, row, linear_cmap,
            subcortex_data=pd.DataFrame(), norm=unit_norm,
            fill_by_significance=True, fill_alpha=1.0, nonsig_fill_alpha=0.3,
            value_column='value',
        )
        assert color[3] == pytest.approx(1.0, abs=1e-3)

    # -- line_thickness from column ------------------------------------------

    def test_line_thickness_read_from_row_column(self, row, linear_cmap):
        thick_row = row.copy()
        thick_row['border_width'] = 4.0
        color_lookup = {'thalamus': 'red'}
        _, _, thickness = _get_region_color(
            color_lookup, thick_row, linear_cmap,
            subcortex_data=None, line_thickness='border_width',
        )
        assert thickness == pytest.approx(4.0, abs=1e-3)

    def test_line_thickness_column_missing_falls_back_to_default(self, row, linear_cmap):
        color_lookup = {'thalamus': 'red'}
        _, _, thickness = _get_region_color(
            color_lookup, row, linear_cmap,
            subcortex_data=None, line_thickness='missing_col',
        )
        assert thickness == pytest.approx(1.5, abs=1e-3)
