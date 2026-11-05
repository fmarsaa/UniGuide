---
title: UniGuide Backend
emoji: 🎓
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# UniGuide – ML Backend API

Random Forest-based university degree programme recommendation system for Kenyan Form Four (KCSE) leavers.

**Author:** Fatuma Omar Marsa (159056), Strathmore University  
**Supervisor:** Deperias Webula Kerre

## Live API

Base URL: `https://fatmaom-uniguide-backend.hf.space`

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check + model status |
| `GET /api/programmes` | All 53 KUCCPS programmes |
| `POST /api/recommend` | Personalised recommendations (auth required) |
| `GET /docs` | Interactive Swagger UI |
