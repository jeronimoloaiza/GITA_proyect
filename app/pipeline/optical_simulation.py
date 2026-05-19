"""Pure optical contrast simulation utilities used by the GUI workspace."""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

MATERIAL_PRESETS: dict[str, dict[str, complex | float]] = {
    "Graphene": {
        "flake_index": 2.6 - 1.3j,
        "single_layer_thickness_nm": 0.335,
    },
    "MoS2": {
        "flake_index": 5.0 - 1.0j,
        "single_layer_thickness_nm": 0.65,
    },
}

DEFAULT_INCIDENT_MEDIUM_INDEX: complex = 1.0
DEFAULT_OXIDE_INDEX: complex = 1.46
DEFAULT_SUBSTRATE_INDEX: complex = 5.6 - 0.4j
DEFAULT_CLIP_RANGE: tuple[float, float] = (-50.0, 50.0)
DEFAULT_SAMPLES: int = 300


def parse_complex_index(text: str, default: Optional[complex] = None) -> complex:
    """Parse a complex refractive index from text, using ``default`` if empty."""

    normalized = text.strip().replace(" ", "")
    normalized = normalized[1:-1] if normalized.startswith("(") and normalized.endswith(")") else normalized

    if normalized == "":
        if default is not None:
            return complex(default)
        raise ValueError("A complex refractive index is required.")

    normalized = {"j": "1j", "+j": "+1j", "-j": "-1j"}.get(normalized, normalized)

    try:
        return complex(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid complex index: {text!r}") from exc


def get_material_preset(material_name: str) -> dict[str, complex | float]:
    """Return the preset optical constants for a supported material name."""

    try:
        return MATERIAL_PRESETS[material_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported material preset: {material_name}") from exc


def reflected_intensity(
    wavelength_nm,
    ambient_index,
    flake_index,
    oxide_index,
    substrate_index,
    flake_thickness_nm,
    oxide_thickness_nm
):
    """
    Calcula la intensidad reflejada para un sistema:
      aire / flake / SiO2 / Si
    usando las ecuaciones de Fresnel para incidencia normal.

    Parámetros
    ----------
    wavelength_nm : float o array
        Longitud de onda en nm.

    ambient_index, flake_index, oxide_index, substrate_index : complex
        Índices de complejos de:
        aire, flake, SiO2, Si, respectivamente

    flake_thickness_nm, oxide_thickness_nm : float
        Espesor del flake y SiO2 en nm, respectivamente

    Retorna
    -------
    float o array
        Intensidad reflejada normalizada (entre 0 y 1).
    """

    wavelength_nm = np.asarray(
        wavelength_nm,
        dtype=np.complex128
    )

    # COEFICIENTES DE FRESNEL
    r1 = (ambient_index - flake_index)/(ambient_index + flake_index)
    r2 = (flake_index - oxide_index)/(flake_index + oxide_index)
    r3 = (oxide_index - substrate_index)/(oxide_index + substrate_index)

    # FASES ÓPTICAS
    phi1 = 2*np.pi*flake_index * flake_thickness_nm/wavelength_nm
    phi2 = 2*np.pi*oxide_index * oxide_thickness_nm/wavelength_nm

    # COEFICIENTE TOTAL DE REFLEXIÓN
    numerator = (
          r1*np.exp( 1j*(phi1 + phi2))
        + r2*np.exp(-1j*(phi1 - phi2))
        + r3*np.exp(-1j*(phi1 + phi2))
        + r1*r2*r3*np.exp( 1j * (phi1 - phi2))
    )

    denominator = (
          np.exp( 1j*(phi1 + phi2))
        + r1*r2*np.exp(-1j*(phi1 - phi2))
        + r1*r3*np.exp(-1j*(phi1 + phi2))
        + r2*r3*np.exp( 1j*(phi1 - phi2))
    )

    I = np.abs(numerator / denominator)**2

    return I


def optical_contrast(
    wavelength_nm,
    incident_medium_index,
    flake_index,
    oxide_index,
    substrate_index,
    flake_thickness_nm,
    oxide_thickness_nm,
    contrast_in_percent=False,
    clip_contrast=None
):
    """
    Calcula el contraste óptico:
        C = (I_sub - I_flake) / I_sub

    Parameters
    ----------
    contrast_in_percent : bool
        Si True, devuelve el contraste en porcentaje.

    clip_contrast : tuple or None
        Rango para limitar el contraste:
        ej. (-50, 50)
    """

    # INTENSIDAD REFLEJADA CON FLAKE
    I_flake = reflected_intensity(
        wavelength_nm=wavelength_nm,
        ambient_index=incident_medium_index,
        flake_index=flake_index,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        flake_thickness_nm=flake_thickness_nm,
        oxide_thickness_nm=oxide_thickness_nm
    )

    # INTENSIDAD REFLEJADA DEL SUSTRATO
    I_substrate = reflected_intensity(
        wavelength_nm=wavelength_nm,
        ambient_index=incident_medium_index,
        flake_index=1,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        flake_thickness_nm=0,
        oxide_thickness_nm=oxide_thickness_nm
    )

    # CONTRASTE ÓPTICO
    C = (I_substrate - I_flake) / I_substrate

    # OPCIONAL: PORCENTAJE
    if contrast_in_percent:
      C *= 100

    # OPCIONAL: CLIPPING
    if clip_contrast is not None:
        C = np.clip(
            C,
            clip_contrast[0],
            clip_contrast[1]
        )

    return np.real(C)


def _style_axis(axis: Axes) -> None:
    """Apply consistent publication-style formatting to an axis.

    Parameters
    ----------
    axis : matplotlib.axes.Axes
        Axis to format.

    Returns
    -------
    None
        The axis is modified in place.
    """

    axis.grid(True)


def contrast_vs_wavelength(
    wavelengths_nm,
    incident_medium_index,
    flake_index,
    oxide_index,
    substrate_index,
    flake_thickness_nm,
    oxide_thickness_nm,
    contrast_in_percent=False,
    clip_contrast=None,
    show: bool = True,
):
    """
    Grafica el contraste óptico en función de la longitud de onda.
    """

    wavelengths_nm = np.asarray(wavelengths_nm, dtype=float)

    contrast_values = optical_contrast(
        wavelength_nm=wavelengths_nm,
        incident_medium_index=incident_medium_index,
        flake_index=flake_index,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        flake_thickness_nm=flake_thickness_nm,
        oxide_thickness_nm=oxide_thickness_nm,
        contrast_in_percent=contrast_in_percent,
        clip_contrast=clip_contrast
    )

    contrast_values = np.asarray(contrast_values, dtype=float)
    max_index = int(np.nanargmax(contrast_values))
    wavelength_max = wavelengths_nm[max_index]
    contrast_max = contrast_values[max_index]

    fig, axis = plt.subplots(figsize=(8, 5))
    axis.plot(wavelengths_nm, contrast_values, color="#2ca02c", linewidth=2.0)
    axis.plot(
        wavelength_max,
        contrast_max,
        "ro",
        label=fr"Máximo en $\lambda = {wavelength_max:.2f}$ nm",
    )
    axis.set_xlabel("Longitud de onda (nm)")
    axis.set_ylabel("Contraste óptico")
    axis.set_title("Contraste óptico vs longitud de onda")
    _style_axis(axis)
    axis.legend()
    fig.tight_layout()
    if show:
        plt.show()

    return fig


def plot_contrast_vs_layers(
    layer_numbers: np.ndarray,
    single_layer_thickness_nm: float,
    wavelength_nm: float,
    incident_medium_index,
    flake_index: complex,
    oxide_index: complex,
    substrate_index: complex,
    oxide_thickness_nm: float,
    clip_range: Optional[tuple[float, float]] = DEFAULT_CLIP_RANGE,
    show: bool = True,
) -> tuple[Figure, Axes]:
    """Plot optical contrast versus layer count and highlight the maximum.

    The layer counts are converted to thickness using ``single_layer_thickness_nm``.
    """

    layer_numbers = np.asarray(layer_numbers, dtype=float)
    flake_thicknesses_nm = layer_numbers * single_layer_thickness_nm

    contrasts_percent = []
    for flake_thickness_nm in flake_thicknesses_nm:
        contrast_value = optical_contrast(
            wavelength_nm=wavelength_nm,
            incident_medium_index=incident_medium_index,
            flake_index=flake_index,
            oxide_index=oxide_index,
            substrate_index=substrate_index,
            flake_thickness_nm=flake_thickness_nm,
            oxide_thickness_nm=oxide_thickness_nm,
            contrast_in_percent=True,
            clip_contrast=clip_range,
        )
        contrasts_percent.append(contrast_value)

    contrasts_percent = np.asarray(contrasts_percent, dtype=float)

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(layer_numbers, contrasts_percent, "o-", linewidth=2.0, color="#2ca02c")
    axis.set_xlabel("Número de capas")
    axis.set_ylabel("Contraste óptico")
    axis.set_title(
        fr"Contraste óptico vs número de capas\n"
        fr"$\lambda = {wavelength_nm:.2f}$ nm"
    )
    axis.set_xticks(layer_numbers)
    max_index = int(np.nanargmax(contrasts_percent))
    axis.plot(
        layer_numbers[max_index],
        contrasts_percent[max_index],
        "ro",
        label=fr"Máximo en {layer_numbers[max_index]:.0f} capas",
    )
    _style_axis(axis)
    axis.legend()
    figure.tight_layout()
    if show:
        plt.show()
    return figure, axis


def contrast_vs_lambda_and_thickness(
    wavelengths_nm,
    incident_medium_index,
    flake_index,
    oxide_index,
    substrate_index,
    flake_thickness_nm,
    oxide_thicknesses_nm,
    layers: int = 1,
    contrast_in_percent: bool = False,
    clip_contrast=None,
    show: bool = True,
) -> tuple[Figure, Axes]:
    """Plot optical contrast versus wavelength and SiO2 thickness."""

    wavelengths_nm = np.asarray(wavelengths_nm, dtype=float)
    oxide_thicknesses_nm = np.asarray(oxide_thicknesses_nm, dtype=float)
    contrast_map = np.zeros((wavelengths_nm.size, oxide_thicknesses_nm.size), dtype=float)

    for wavelength_index, wavelength_value_nm in enumerate(wavelengths_nm):
        for oxide_index_value, oxide_thickness_value_nm in enumerate(oxide_thicknesses_nm):
            contrast_map[wavelength_index, oxide_index_value] = optical_contrast(
                wavelength_nm=wavelength_value_nm,
                incident_medium_index=incident_medium_index,
                flake_index=flake_index,
                oxide_index=oxide_index,
                substrate_index=substrate_index,
                flake_thickness_nm=flake_thickness_nm,
                oxide_thickness_nm=oxide_thickness_value_nm,
                contrast_in_percent=contrast_in_percent,
                clip_contrast=clip_contrast,
            )

    figure, axis = plt.subplots(figsize=(10, 6))
    image = axis.imshow(
        contrast_map,
        extent=[
            oxide_thicknesses_nm.min(),
            oxide_thicknesses_nm.max(),
            wavelengths_nm.min(),
            wavelengths_nm.max(),
        ],
        origin="lower",
        aspect="auto",
        cmap="seismic",
    )
    axis.set_xlabel(r"Espesor SiO$_2$ (nm)")
    axis.set_ylabel("Longitud de onda (nm)")
    axis.set_title(f"Contraste óptico\n{layers} capa(s)")
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Contraste óptico (%)")
    _style_axis(axis)
    figure.tight_layout()
    if show:
        plt.show()
    return figure, axis


def contrast_vs_layers_and_lambda(
    wavelengths_nm,
    incident_medium_index,
    flake_index,
    oxide_index,
    substrate_index,
    flake_thicknesses_nm,
    oxide_thickness_nm,
    contrast_in_percent: bool = False,
    clip_contrast=None,
    show: bool = True,
) -> tuple[Figure, Axes]:
    """Plot optical contrast versus wavelength and flake thickness."""

    wavelengths_nm = np.asarray(wavelengths_nm, dtype=float)
    flake_thicknesses_nm = np.asarray(flake_thicknesses_nm, dtype=float)
    contrast_map = np.zeros((flake_thicknesses_nm.size, wavelengths_nm.size), dtype=float)

    for thickness_index, flake_thickness_value_nm in enumerate(flake_thicknesses_nm):
        for wavelength_index, wavelength_value_nm in enumerate(wavelengths_nm):
            contrast_map[thickness_index, wavelength_index] = optical_contrast(
                wavelength_nm=wavelength_value_nm,
                incident_medium_index=incident_medium_index,
                flake_index=flake_index,
                oxide_index=oxide_index,
                substrate_index=substrate_index,
                flake_thickness_nm=flake_thickness_value_nm,
                oxide_thickness_nm=oxide_thickness_nm,
                contrast_in_percent=contrast_in_percent,
                clip_contrast=clip_contrast,
            )

    wavelength_grid, thickness_grid = np.meshgrid(wavelengths_nm, flake_thicknesses_nm)

    figure, axis = plt.subplots(figsize=(9, 5))
    filled = axis.contourf(
        wavelength_grid,
        thickness_grid,
        contrast_map,
        levels=10,
        cmap="bone_r",
    )
    axis.set_xlabel(r"$\lambda$ (nm)")
    axis.set_ylabel("Flake thickness (nm)")
    axis.set_title("Optical contrast on SiO$_2$/Si")
    colorbar = figure.colorbar(filled, ax=axis)
    colorbar.set_label("Optical contrast (%)")
    _style_axis(axis)
    figure.tight_layout()
    if show:
        plt.show()
    return figure, axis


def generate_simulation_figures(
    incident_medium_index: complex,
    flake_index: complex,
    oxide_index: complex,
    substrate_index: complex,
    single_layer_thickness_nm: float,
    selected_layers: int,
    layer_min: int,
    layer_max: int,
    wavelength_nm: float,
    wavelength_min_nm: float,
    wavelength_max_nm: float,
    oxide_thickness_nm: float,
    oxide_min_nm: float,
    oxide_max_nm: float,
    sample_count: int = DEFAULT_SAMPLES,
    clip_range: Optional[tuple[float, float]] = DEFAULT_CLIP_RANGE,
) -> dict[str, Figure]:
    """Generate the four optical-contrast figures used by the GUI."""

    wavelengths_nm = np.linspace(wavelength_min_nm, wavelength_max_nm, sample_count)
    oxide_thickness_nm_values = np.linspace(oxide_min_nm, oxide_max_nm, sample_count)
    layer_numbers = np.arange(layer_min, layer_max + 1, dtype=int)
    selected_flake_thickness_nm = selected_layers * single_layer_thickness_nm

    wavelength_contrast_figure = contrast_vs_wavelength(
        wavelengths_nm=wavelengths_nm,
        incident_medium_index=incident_medium_index,
        flake_index=flake_index,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        flake_thickness_nm=selected_flake_thickness_nm,
        oxide_thickness_nm=oxide_thickness_nm,
        contrast_in_percent=True,
        clip_contrast=clip_range,
        show=False,
    )

    layer_contrast_figure, _ = plot_contrast_vs_layers(
        layer_numbers=layer_numbers,
        single_layer_thickness_nm=single_layer_thickness_nm,
        wavelength_nm=wavelength_nm,
        incident_medium_index=incident_medium_index,
        flake_index=flake_index,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        oxide_thickness_nm=oxide_thickness_nm,
        clip_range=clip_range,
        show=False,
    )

    wavelength_oxide_figure, _ = contrast_vs_lambda_and_thickness(
        wavelengths_nm=wavelengths_nm,
        incident_medium_index=incident_medium_index,
        flake_index=flake_index,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        flake_thickness_nm=selected_flake_thickness_nm,
        oxide_thicknesses_nm=oxide_thickness_nm_values,
        layers=selected_layers,
        contrast_in_percent=True,
        clip_contrast=clip_range,
        show=False,
    )

    flake_thicknesses_nm = layer_numbers.astype(float) * single_layer_thickness_nm
    wavelength_layers_figure, _ = contrast_vs_layers_and_lambda(
        wavelengths_nm=wavelengths_nm,
        incident_medium_index=incident_medium_index,
        flake_index=flake_index,
        oxide_index=oxide_index,
        substrate_index=substrate_index,
        flake_thicknesses_nm=flake_thicknesses_nm,
        oxide_thickness_nm=oxide_thickness_nm,
        contrast_in_percent=True,
        clip_contrast=clip_range,
        show=False,
    )

    return {
        "wavelength_contrast": wavelength_contrast_figure,
        "layer_contrast": layer_contrast_figure,
        "wavelength_oxide_heatmap": wavelength_oxide_figure,
        "wavelength_layers_heatmap": wavelength_layers_figure,
    }
