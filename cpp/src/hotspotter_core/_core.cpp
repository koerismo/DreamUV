#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>

#include "hotspot.h"
#include "hotspot.cpp"

namespace nb = nanobind;
namespace hs = HotSpot;

// float square(float x) { return x * x; }

NB_MODULE(_core, m) {
    // m.def("square", &square);

    m.def("fit_rect_to_surface", &hs::FitRectToSurface, nb::arg("rects"), nb::arg("surf_dims"), nb::arg("out_result"));
    m.def("get_score", &hs::GetScore, nb::arg("dims_surf"), nb::arg("rect"), nb::arg("out_result"));

    nb::enum_<hs::RectFlags_t>(m, "RectFlags_t", nb::is_flag())
        .value("enable_rotation", hs::RectFlags_t::enable_rotation)
        .value("enable_reflection", hs::RectFlags_t::enable_reflection)
        .value("alt_group", hs::RectFlags_t::alt_group)
        .value("tile_x", hs::RectFlags_t::tile_x)
        .value("tile_y", hs::RectFlags_t::tile_y)
        .value("tile_x_y", hs::RectFlags_t::tile_x_y)
        .export_values()
        ;

    nb::class_<hs::Vec2f>(m, "Vec2f")
       .def(nb::init<double, double>(), nb::arg("x"), nb::arg("y"))
       .def_prop_rw("x",
                [](hs::Vec2f &t) { return t.x; },
                [](hs::Vec2f &t, double v) { t.x = v; }
            )
       .def_prop_rw("y",
                [](hs::Vec2f &t) { return t.y; },
                [](hs::Vec2f &t, double v) { t.y = v; }
            )
       .def("swapped", &hs::Vec2f::Swapped)
       .def("dot", &hs::Vec2f::Dot)
       .def("normalized", &hs::Vec2f::Normalized)
       ;
    
    nb::class_<hs::Vec2i>(m, "Vec2i")
       .def(nb::init<int, int>(), nb::arg("x"), nb::arg("y"))
       .def_prop_rw("x",
                [](hs::Vec2i &t) { return t.x; },
                [](hs::Vec2i &t, int v) { t.x = v; }
            )
       .def_prop_rw("y",
                [](hs::Vec2i &t) { return t.y; },
                [](hs::Vec2i &t, int v) { t.y = v; }
            )
       .def("swapped", &hs::Vec2i::Swapped)
       ;
    
    nb::class_<hs::Rect>(m, "Rect")
       .def(nb::init<uint16_t, hs::Vec2f, hs::Vec2f>(), nb::arg("flags"), nb::arg("mins"), nb::arg("maxs"))
       .def_prop_rw("mins",
                    [](hs::Rect &t) { return t.mins; },
                    [](hs::Rect &t, hs::Vec2f v) { t.mins = v; }
                )
       .def_prop_rw("maxs",
                    [](hs::Rect &t) { return t.maxs; },
                    [](hs::Rect &t, hs::Vec2f v) { t.maxs = v; }
                )
       .def("get_width", &hs::Rect::GetWidth)
       .def("get_height", &hs::Rect::GetHeight)
       .def("can_rotate", &hs::Rect::CanRotate)
       .def("can_reflect", &hs::Rect::CanReflect)
       .def("can_tile", &hs::Rect::CanTile)
       .def("can_tile_x", &hs::Rect::CanTileX)
       .def("can_tile_y", &hs::Rect::CanTileY)
       .def("is_alt_group", &hs::Rect::IsAltGroup)
       ;
    
    nb::class_<hs::RectFitResult>(m, "RectFitResult")
       .def(nb::init<int, bool>(), nb::arg("rect_idx"), nb::arg("rotated"))
       .def_prop_rw("rect_idx",
                    [](hs::RectFitResult &t) { return t.rect_idx; },
                    [](hs::RectFitResult &t, int v) { t.rect_idx = v; }
                )
       .def_prop_rw("tiling",
                    [](hs::RectFitResult &t) { return t.tiling; },
                    [](hs::RectFitResult &t, hs::Vec2i v) { t.tiling = v; }
                )
       .def_prop_rw("rotated",
                    [](hs::RectFitResult &t) { return t.rotated; },
                    [](hs::RectFitResult &t, bool v) { t.rotated = v; }
                )
       .def_prop_rw("score",
                    [](hs::RectFitResult &t) { return t.score; },
                    [](hs::RectFitResult &t, float v) { t.score = v; }
                )
       ;

    nb::class_<hs::RectFile>(m, "RectFile")
       .def(nb::init<uint8_t, hs::Vec2i, std::vector<HotSpot::Rect>>(), nb::arg("version"), nb::arg("tex_size"), nb::arg("rects"))
       .def_prop_rw("flags",
                    [](hs::RectFile &t) { return t.flags; },
                    [](hs::RectFile &t, uint8_t v) { t.flags = v; }
                )
       .def_prop_ro("tex_size",
                    [](hs::RectFile &t) { return t.tex_size; }
                )
       .def_prop_ro("rects",
                    [](hs::RectFile &t) { return t.rects; }
                )
       ;
}
