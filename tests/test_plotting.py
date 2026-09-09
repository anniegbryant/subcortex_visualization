import pytest
import numpy as np
import pandas as pd
import matplotlib.colors as mcolors
from matplotlib.figure import Figure

from subcortex_visualization.plotting import plot_subcortical_data
from subcortex_visualization.utils import get_atlas_regions


ALL_ATLASES = [
    'aseg_subcortex',
    'Melbourne_S1',
    'Melbourne_S2',
    'Melbourne_S3',
    'Melbourne_S4',
    'Melbourne_S1_7T',
    'Melbourne_S2_7T',
    'Melbourne_S3_7T',
    'Melbourne_S4_7T',
    'AICHA_subcortex',
    'Brainnetome_subcortex',
    'CIT168_subcortex',
    'Thalamus_HCP',
    'Thalamus_THOMAS',
    'Brainstem_Navigator',
    'SUIT_cerebellar_lobule',
]


class TestDefaults:
    """Default call with no user data produces a Figure."""

    def test_returns_figure_when_show_false(self):
        fig = plot_subcortical_data(show_figure=False)
        assert isinstance(fig, Figure)

    def test_show_true_returns_none(self):
        result = plot_subcortical_data(show_figure=True)
        assert result is None

    def test_default_has_axes(self):
        fig = plot_subcortical_data(show_figure=False)
        assert len(fig.axes) > 0


class TestAllAtlasesRender:
    """Every built-in atlas renders without error for default parameters."""

    @pytest.mark.parametrize('atlas', ALL_ATLASES)
    def test_atlas_renders(self, atlas):
        fig = plot_subcortical_data(atlas=atlas, show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_tian_alias_resolves(self):
        """Tian_S* is a backward-compatible alias for Melbourne_S*."""
        fig = plot_subcortical_data(atlas='Tian_S1', show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_tian_7t_alias_resolves(self):
        """Tian_S*_7T is a backward-compatible alias for Melbourne_S*_7T."""
        fig = plot_subcortical_data(atlas='Tian_S1_7T', show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    @pytest.mark.parametrize('scale', [1, 2, 3, 4])
    def test_melbourne_7t_bilateral(self, scale):
        fig = plot_subcortical_data(
            atlas=f'Melbourne_S{scale}_7T', hemisphere='both',
            show_figure=False, show_legend=True,
        )
        assert isinstance(fig, Figure)

    def test_invalid_atlas_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            plot_subcortical_data(atlas='nonexistent_atlas_xyz', show_figure=False)


class TestHemisphereOptions:
    """Hemisphere argument controls which side(s) are rendered."""

    def test_left_hemisphere(self):
        fig = plot_subcortical_data(hemisphere='L', show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_right_hemisphere(self):
        fig = plot_subcortical_data(hemisphere='R', show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_both_hemispheres(self):
        fig = plot_subcortical_data(hemisphere='both', show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_suit_forces_both_and_prints_warning(self, capsys):
        fig = plot_subcortical_data(
            atlas='SUIT_cerebellar_lobule', hemisphere='L',
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)
        captured = capsys.readouterr()
        assert 'both' in captured.out.lower()


class TestViewAngles:
    """The views argument selects which anatomical faces to render."""

    @pytest.mark.parametrize('views', [
        ['medial'],
        ['lateral'],
        ['superior'],
        ['inferior'],
        ['medial', 'lateral'],
        ['superior', 'inferior'],
        ['medial', 'lateral', 'superior', 'inferior'],
    ])
    def test_view_combinations(self, views):
        fig = plot_subcortical_data(views=views, show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_all_four_views_thalamus_thomas(self):
        cmap = mcolors.LinearSegmentedColormap.from_list('test', ['white', '#d14662'])
        fig = plot_subcortical_data(
            atlas='Thalamus_THOMAS', cmap=cmap, hemisphere='both',
            views=['lateral', 'medial', 'superior', 'inferior'],
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_all_four_views_brainstem(self):
        cmap = mcolors.LinearSegmentedColormap.from_list('test', ['white', '#c8499b'])
        fig = plot_subcortical_data(
            atlas='Brainstem_Navigator', cmap=cmap, hemisphere='both',
            views=['lateral', 'medial', 'superior', 'inferior'],
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)


class TestColormapOptions:
    """Colormaps can be strings, Colormap objects, or left as None for the default."""

    def test_string_colormap(self):
        fig = plot_subcortical_data(cmap='plasma', show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_colormap_object(self):
        cmap = mcolors.LinearSegmentedColormap.from_list('bwr', ['blue', 'white', 'red'])
        fig = plot_subcortical_data(cmap=cmap, show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_none_uses_viridis_default(self):
        fig = plot_subcortical_data(cmap=None, show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_aicha_plasma_both(self):
        fig = plot_subcortical_data(
            atlas='AICHA_subcortex', cmap='plasma', hemisphere='both',
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_brainnetome_hsv_both(self):
        fig = plot_subcortical_data(
            atlas='Brainnetome_subcortex', cmap='hsv', hemisphere='both',
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)


class TestFillAlpha:
    """fill_alpha controls global opacity of all regions."""

    @pytest.mark.parametrize('fill_alpha', [0.2, 0.4, 0.6, 0.8, 1.0])
    def test_alpha_range(self, fill_alpha):
        fig = plot_subcortical_data(
            atlas='Melbourne_S2', fill_alpha=fill_alpha,
            cmap='plasma', show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)


class TestContinuousData:
    """plot_subcortical_data maps a numeric value column through the colormap."""

    def test_bilateral_continuous_data(self, aseg_continuous_data):
        fig = plot_subcortical_data(
            subcortex_data=aseg_continuous_data,
            atlas='aseg_subcortex', hemisphere='both',
            cmap='viridis', show_figure=False,
        )
        assert isinstance(fig, Figure)

    def test_left_hemisphere_only(self, aseg_continuous_data):
        left = aseg_continuous_data[aseg_continuous_data['Hemisphere'] == 'L']
        fig = plot_subcortical_data(
            subcortex_data=left, atlas='aseg_subcortex',
            hemisphere='L', show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_custom_value_column(self, aseg_regions):
        np.random.seed(7)
        data = pd.DataFrame({
            'region': aseg_regions,
            'my_stat': np.random.normal(0, 1, len(aseg_regions)),
            'Hemisphere': 'L',
        })
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex',
            value_column='my_stat', hemisphere='L',
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_nan_values_use_na_fill(self, aseg_regions):
        data = pd.DataFrame({
            'region': aseg_regions,
            'value': np.nan,
            'Hemisphere': 'L',
        })
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex',
            hemisphere='L', NA_fill='#ff0000',
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_explicit_vmin_vmax(self, aseg_continuous_data):
        fig = plot_subcortical_data(
            subcortex_data=aseg_continuous_data,
            atlas='aseg_subcortex', hemisphere='both',
            vmin=-2, vmax=2,
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)


class TestDiscreteCategoricalData:
    """A discrete/categorical value_column colors regions by category (fill_domain)
    instead of falling back to a continuous colormap."""

    def test_string_categories_render(self, aseg_categorical_data):
        fig = plot_subcortical_data(
            subcortex_data=aseg_categorical_data,
            atlas='aseg_subcortex', hemisphere='L',
            show_figure=False, show_legend=True, fill_title='Group',
        )
        assert isinstance(fig, Figure)

    def test_legend_shows_sorted_category_labels(self, aseg_categorical_data):
        fig = plot_subcortical_data(
            subcortex_data=aseg_categorical_data,
            atlas='aseg_subcortex', hemisphere='L',
            show_figure=False, show_legend=True,
        )
        labels = [t.get_text() for t in fig.legends[-1].get_texts()]
        assert labels == sorted(aseg_categorical_data['value'].unique())

    def test_categorical_dtype_preserves_level_order_in_legend(self, aseg_regions):
        values = (['low', 'mid', 'high'] * len(aseg_regions))[:len(aseg_regions)]
        data = pd.DataFrame({
            'region': aseg_regions,
            'value': pd.Categorical(values, categories=['high', 'mid', 'low'], ordered=True),
            'Hemisphere': 'L',
        })
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex', hemisphere='L',
            show_figure=False, show_legend=True,
        )
        labels = [t.get_text() for t in fig.legends[-1].get_texts()]
        assert labels == ['high', 'mid', 'low']

    def test_regions_sharing_category_get_same_color(self, aseg_regions):
        # Every region is assigned the same single category, so every patch
        # across every panel should end up the same facecolor.
        data = pd.DataFrame({
            'region': aseg_regions,
            'value': 'only_group',
            'Hemisphere': 'L',
        })
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex', hemisphere='L',
            show_figure=False, show_legend=False,
        )
        patch_colors = {
            tuple(patch.get_facecolor())
            for ax in fig.axes for patch in ax.patches
        }
        assert len(patch_colors) == 1

    def test_unmatched_region_uses_na_fill(self, aseg_regions):
        # Omit one region from the supplied data entirely.
        data = pd.DataFrame({
            'region': aseg_regions,
            'value': 'A',
            'Hemisphere': 'L',
        })
        data = data.iloc[1:]
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex', hemisphere='L',
            NA_fill='#ff0000', show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)


class TestDivergingColormap:
    """midpoint=0 creates a symmetric TwoSlopeNorm centered on that value."""

    def test_midpoint_zero(self, aseg_continuous_data):
        cmap = mcolors.LinearSegmentedColormap.from_list('bwr', ['blue', 'white', 'red'])
        fig = plot_subcortical_data(
            subcortex_data=aseg_continuous_data,
            atlas='aseg_subcortex', hemisphere='both',
            cmap=cmap, midpoint=0,
            show_figure=False,
        )
        assert isinstance(fig, Figure)

    def test_midpoint_with_explicit_bounds(self, aseg_continuous_data):
        fig = plot_subcortical_data(
            subcortex_data=aseg_continuous_data,
            atlas='aseg_subcortex', hemisphere='both',
            midpoint=0, vmin=-3, vmax=3,
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)


class TestSignificanceTransparency:
    """fill_by_significance dims non-significant regions (p >= 0.05)."""

    def test_fill_by_significance_suit(self, suit_significance_data):
        fig = plot_subcortical_data(
            atlas='SUIT_cerebellar_lobule',
            subcortex_data=suit_significance_data,
            hemisphere='both', midpoint=0, cmap='PiYG',
            fill_by_significance=True, nonsig_fill_alpha=0.5,
            line_thickness=3,
            show_figure=False,
        )
        assert isinstance(fig, Figure)

    def test_fill_by_significance_aseg(self, aseg_continuous_data):
        data = aseg_continuous_data.copy()
        np.random.seed(1)
        data['p_value'] = np.random.uniform(0, 1, len(data))
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex',
            hemisphere='both', fill_by_significance=True,
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_fill_by_significance_without_p_value_raises(self, aseg_regions):
        data = pd.DataFrame({
            'region': aseg_regions,
            'value': np.random.normal(0, 1, len(aseg_regions)),
            'Hemisphere': 'L',
        })
        with pytest.raises(ValueError, match='p_value'):
            plot_subcortical_data(
                subcortex_data=data, atlas='aseg_subcortex',
                fill_by_significance=True, show_figure=False,
            )

    def test_fill_by_significance_without_subcortex_data_raises(self):
        with pytest.raises(ValueError, match='p_value'):
            plot_subcortical_data(fill_by_significance=True, show_figure=False)


class TestLegend:
    """show_legend controls whether a legend or colorbar is appended."""

    def test_legend_hidden(self):
        fig = plot_subcortical_data(show_figure=False, show_legend=False)
        assert isinstance(fig, Figure)

    def test_discrete_legend_no_data(self):
        fig = plot_subcortical_data(show_figure=False, show_legend=True)
        assert isinstance(fig, Figure)

    def test_colorbar_with_continuous_data(self, aseg_continuous_data):
        fig = plot_subcortical_data(
            subcortex_data=aseg_continuous_data,
            atlas='aseg_subcortex', hemisphere='L',
            show_figure=False, show_legend=True,
        )
        assert isinstance(fig, Figure)

    def test_fill_title_accepted(self):
        fig = plot_subcortical_data(
            fill_title='My custom label',
            show_figure=False, show_legend=True,
        )
        assert isinstance(fig, Figure)


class TestLineStyle:
    """line_color and line_thickness style the region outlines."""

    def test_custom_line_color(self):
        fig = plot_subcortical_data(
            line_color='red', show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_custom_line_thickness(self):
        fig = plot_subcortical_data(
            line_thickness=3.0, show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)

    def test_line_thickness_from_column(self, aseg_regions):
        np.random.seed(5)
        data = pd.DataFrame({
            'region': aseg_regions,
            'value': np.random.normal(0, 1, len(aseg_regions)),
            'thickness': np.random.uniform(0.5, 3.0, len(aseg_regions)),
            'Hemisphere': 'L',
        })
        fig = plot_subcortical_data(
            subcortex_data=data, atlas='aseg_subcortex',
            hemisphere='L', line_thickness='thickness',
            show_figure=False, show_legend=False,
        )
        assert isinstance(fig, Figure)
