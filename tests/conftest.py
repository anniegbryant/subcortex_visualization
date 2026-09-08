import matplotlib
matplotlib.use('Agg')

import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from subcortex_visualization.utils import get_atlas_regions


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


@pytest.fixture
def aseg_regions():
    return get_atlas_regions('aseg_subcortex')


@pytest.fixture
def aseg_continuous_data(aseg_regions):
    np.random.seed(42)
    left = pd.DataFrame({
        'region': aseg_regions,
        'value': np.random.normal(0, 1, len(aseg_regions)),
        'Hemisphere': 'L',
    })
    right = pd.DataFrame({
        'region': aseg_regions,
        'value': np.random.normal(0, 1, len(aseg_regions)),
        'Hemisphere': 'R',
    })
    return pd.concat([left, right], ignore_index=True)


@pytest.fixture
def suit_continuous_data():
    np.random.seed(42)
    hemi_regions, vermis_regions = get_atlas_regions('SUIT_cerebellar_lobule')
    data = pd.DataFrame({
        'region': np.concatenate([hemi_regions, hemi_regions, vermis_regions]),
        'Hemisphere': (
            ['L'] * len(hemi_regions) +
            ['R'] * len(hemi_regions) +
            ['V'] * len(vermis_regions)
        ),
    })
    data['value'] = np.random.normal(0, 1, len(data))
    return data


@pytest.fixture
def aseg_categorical_data(aseg_regions):
    np.random.seed(3)
    return pd.DataFrame({
        'region': aseg_regions,
        'value': np.random.choice(['low', 'mid', 'high'], size=len(aseg_regions)),
        'Hemisphere': 'L',
    })


@pytest.fixture
def suit_significance_data(suit_continuous_data):
    data = suit_continuous_data.copy()
    np.random.seed(128)
    data['p_value'] = np.random.uniform(0.05, 1.0, len(data))
    largest = np.argsort(np.abs(data['value']))[-4:]
    data.loc[largest, 'p_value'] = 0.01
    return data
