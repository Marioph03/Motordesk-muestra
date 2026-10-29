from pydantic import BaseModel


class DashboardChartResponse(BaseModel):

    mes: str

    importe: float
"""Serie temporal simplificada para las gráficas del Dashboard."""
