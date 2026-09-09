import pytest
import numpy as np

from subcortex_visualization.utils import get_atlas_regions


STANDARD_ATLASES = [
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
]


class TestGetAtlasRegionsStandard:
    """get_atlas_regions returns a 1-D string array for all standard atlases."""

    @pytest.mark.parametrize('atlas', STANDARD_ATLASES)
    def test_returns_1d_array(self, atlas):
        regions = get_atlas_regions(atlas)
        assert isinstance(regions, np.ndarray)
        assert regions.ndim == 1

    @pytest.mark.parametrize('atlas', STANDARD_ATLASES)
    def test_nonempty(self, atlas):
        regions = get_atlas_regions(atlas)
        assert len(regions) > 0

    @pytest.mark.parametrize('atlas', STANDARD_ATLASES)
    def test_regions_are_strings(self, atlas):
        regions = get_atlas_regions(atlas)
        assert all(isinstance(r, str) for r in regions)

    @pytest.mark.parametrize('atlas', STANDARD_ATLASES)
    def test_no_duplicate_regions(self, atlas):
        regions = get_atlas_regions(atlas)
        assert len(regions) == len(set(regions))

    def test_aseg_expected_regions(self):
        regions = get_atlas_regions('aseg_subcortex')
        expected = {'thalamus', 'caudate', 'putamen', 'pallidum',
                    'hippocampus', 'amygdala', 'accumbens'}
        assert set(regions) == expected

    def test_aseg_seven_regions(self):
        assert len(get_atlas_regions('aseg_subcortex')) == 7

    def test_melbourne_s1_eight_regions(self):
        assert len(get_atlas_regions('Melbourne_S1')) == 8

    def test_melbourne_region_counts_increase_with_scale(self):
        counts = [len(get_atlas_regions(f'Melbourne_S{i}')) for i in range(1, 5)]
        assert counts == sorted(counts)

    def test_melbourne_7t_s1_eight_regions(self):
        assert len(get_atlas_regions('Melbourne_S1_7T')) == 8

    def test_melbourne_7t_region_counts_increase_with_scale(self):
        counts = [len(get_atlas_regions(f'Melbourne_S{i}_7T')) for i in range(1, 5)]
        assert counts == sorted(counts)

    def test_melbourne_7t_region_counts_differ_from_3t(self):
        # 7T resegmentation yields a different (generally finer) parcellation
        # than the original 3T atlas at the same nominal scale, except at S1.
        counts_3t = [len(get_atlas_regions(f'Melbourne_S{i}')) for i in range(1, 5)]
        counts_7t = [len(get_atlas_regions(f'Melbourne_S{i}_7T')) for i in range(1, 5)]
        assert counts_7t != counts_3t


class TestGetAtlasRegionsSuit:
    """SUIT cerebellar lobule returns a (hemisphere_regions, vermis_regions) tuple."""

    def test_returns_tuple(self):
        result = get_atlas_regions('SUIT_cerebellar_lobule')
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_hemisphere_regions_is_array(self):
        hemi, _ = get_atlas_regions('SUIT_cerebellar_lobule')
        assert isinstance(hemi, np.ndarray)

    def test_vermis_regions_is_array(self):
        _, vermis = get_atlas_regions('SUIT_cerebellar_lobule')
        assert isinstance(vermis, np.ndarray)

    def test_hemisphere_expected_regions(self):
        hemi, _ = get_atlas_regions('SUIT_cerebellar_lobule')
        expected = {'IV', 'V', 'VI', 'Crus_I', 'Crus_II', 'VIIb', 'VIIIa', 'VIIIb', 'IX', 'X'}
        assert set(hemi) == expected

    def test_vermis_expected_regions(self):
        _, vermis = get_atlas_regions('SUIT_cerebellar_lobule')
        expected = {'VI', 'Crus_II', 'VIIb', 'VIIIa', 'VIIIb', 'IX', 'X'}
        assert set(vermis) == expected

    def test_hemisphere_ten_regions(self):
        hemi, _ = get_atlas_regions('SUIT_cerebellar_lobule')
        assert len(hemi) == 10

    def test_vermis_seven_regions(self):
        _, vermis = get_atlas_regions('SUIT_cerebellar_lobule')
        assert len(vermis) == 7


class TestGetAtlasRegionsBrainstem:
    """Brainstem Navigator returns a (hemisphere_regions, midline_regions) tuple."""

    def test_returns_tuple(self):
        result = get_atlas_regions('Brainstem_Navigator')
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_hemisphere_regions_is_array(self):
        hemi, _ = get_atlas_regions('Brainstem_Navigator')
        assert isinstance(hemi, np.ndarray)

    def test_midline_regions_is_array(self):
        _, midline = get_atlas_regions('Brainstem_Navigator')
        assert isinstance(midline, np.ndarray)

    def test_hemisphere_regions_nonempty(self):
        hemi, _ = get_atlas_regions('Brainstem_Navigator')
        assert len(hemi) > 0

    def test_midline_regions_nonempty(self):
        _, midline = get_atlas_regions('Brainstem_Navigator')
        assert len(midline) > 0

    def test_known_hemisphere_region_present(self):
        hemi, _ = get_atlas_regions('Brainstem_Navigator')
        assert 'SN1' in hemi
        assert 'RN1' in hemi

    def test_known_midline_region_present(self):
        _, midline = get_atlas_regions('Brainstem_Navigator')
        assert 'PAG' in midline
        assert 'DR' in midline


class TestGetAtlasRegionsInvalid:
    def test_invalid_atlas_raises(self):
        with pytest.raises(Exception):
            get_atlas_regions('this_atlas_does_not_exist_xyz')
