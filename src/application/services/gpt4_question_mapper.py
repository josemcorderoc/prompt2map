import folium
from application.interfaces.question_mapper import QuestionMapper


class GPT4QuestionMapper(QuestionMapper):
    def generate(self, question: str) -> folium.Map:
        # dummy implementation
        campuses = [
            {"name": "Casa Central", "lat": -33.4489, "lon": -70.6610},
            {"name": "Facultad de Ciencias Físicas y Matemáticas", "lat": -33.4169, "lon": -70.6551},
            {"name": "Facultad de Ciencias Químicas y Farmacéuticas", "lat": -33.4586, "lon": -70.6633},
            {"name": "Facultad de Economía y Negocios", "lat": -33.4594, "lon": -70.6350},
            {"name": "Facultad de Medicina", "lat": -33.4196, "lon": -70.6498},
            {"name": "Facultad de Ciencias", "lat": -33.5403, "lon": -70.5739},
            {"name": "Facultad de Filosofía y Humanidades", "lat": -33.4628, "lon": -70.6544},
            {"name": "Facultad de Derecho", "lat": -33.4418, "lon": -70.6551},
            {"name": "Facultad de Ciencias Sociales", "lat": -33.4577, "lon": -70.6640},
            {"name": "Facultad de Arquitectura y Urbanismo", "lat": -33.4513, "lon": -70.6528},
            {"name": "Instituto de la Comunicación e Imagen", "lat": -33.4573, "lon": -70.6602},
        ]

        m = folium.Map(zoom_start=16)
        for campus in campuses:
            folium.Marker(
                [campus["lat"], campus["lon"]], popup=campus["name"], tooltip=campus["name"]
            ).add_to(m)

        m.fit_bounds(m.get_bounds())
        return m
