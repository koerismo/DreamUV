#include <nanobind/nanobind.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/vector.h>
#include <array>

#include "hotspot.h"
#include "hotspot.cpp"

using namespace HotSpot;
namespace nb = nanobind;

NB_MODULE(_core, m) {
    nb::class_<RectFitter>(m, "RectFitter")
        .def(nb::init<>())
        .def(nb::init<WeightConfig>(), nb::arg("config"))
        .def_prop_rw("config",
                [](RectFitter &t) -> auto& { return t.config_; },
                [](RectFitter &t, WeightConfig v) { t.config_ = v; }
            )
        .def("get_score", &RectFitter::GetScore,
                nb::arg("dims_surf"),
                nb::arg("rect"),
                nb::arg("out_result")
            )
        .def("fit_rect_to_surface", &RectFitter::FitRectToSurface,
                nb::arg("rects"),
                nb::arg("dims_surf"),
                nb::arg("out_result")
            )
        .def("get_final_bounds", &RectFitter::GetFinalBounds,
                nb::arg("rect"),
                nb::arg("tiling"),
                nb::arg("inset"),
                nb::arg("out_bounds")
            )
        .def("get_final_transform", [](RectFitter& r, Vec2f& tex_size, Rect& rect, Vec2f& tiling, double inset, int rotation) {
                    std::array<double, 6> matrix_array;
                    auto matrix_ptr = reinterpret_cast<Mat3x2*>(matrix_array.data());
                    r.GetFinalTransform(tex_size, rect, tiling, inset, rotation, *matrix_ptr);
                    return std::move(matrix_array);
                },
                nb::arg("tex_size"),
                nb::arg("rect"),
                nb::arg("tiling"),
                nb::arg("inset"),
                nb::arg("rotation")
            )
        ;

    nb::enum_<RectFlags_t>(m, "RectFlags_t", nb::is_flag())
        .value("enable_rotation", RectFlags_t::enable_rotation)
        .value("enable_reflection", RectFlags_t::enable_reflection)
        .value("alt_group", RectFlags_t::alt_group)
        .value("tile_x", RectFlags_t::tile_x)
        .value("tile_y", RectFlags_t::tile_y)
        .value("tile_x_y", RectFlags_t::tile_x_y)
        .export_values()
        ;

    nb::class_<Vec2f>(m, "Vec2f")
       .def(nb::init<double, double>(), nb::arg("x"), nb::arg("y"))
       .def_prop_rw("x",
                [](Vec2f &t) { return t.x; },
                [](Vec2f &t, double v) { t.x = v; }
            )
       .def_prop_rw("y",
                [](Vec2f &t) { return t.y; },
                [](Vec2f &t, double v) { t.y = v; }
            )
       .def("swapped", &Vec2f::Swapped)
       .def("dot", &Vec2f::Dot)
       .def("normalized", &Vec2f::Normalized)
       ;
    
    nb::class_<Vec2i>(m, "Vec2i")
       .def(nb::init<int, int>(), nb::arg("x"), nb::arg("y"))
       .def_prop_rw("x",
                [](Vec2i &t) { return t.x; },
                [](Vec2i &t, int v) { t.x = v; }
            )
       .def_prop_rw("y",
                [](Vec2i &t) { return t.y; },
                [](Vec2i &t, int v) { t.y = v; }
            )
       .def("swapped", &Vec2i::Swapped)
       ;
    
    nb::class_<Rect>(m, "Rect")
       .def(nb::init<uint16_t, Vec2f, Vec2f>(), nb::arg("flags"), nb::arg("mins"), nb::arg("maxs"))
       .def_prop_rw("flags",
                    [](Rect &t) { return t.flags; },
                    [](Rect &t, uint16_t v) { t.flags = v; }
                )
       .def_prop_rw("mins",
                    [](Rect &t) -> auto& { return t.mins; },
                    [](Rect &t, Vec2f v) { t.mins = v; }
                )
       .def_prop_rw("maxs",
                    [](Rect &t) -> auto& { return t.maxs; },
                    [](Rect &t, Vec2f v) { t.maxs = v; }
                )
       .def("get_width", &Rect::GetWidth)
       .def("get_height", &Rect::GetHeight)
       .def("can_rotate", &Rect::CanRotate)
       .def("can_reflect", &Rect::CanReflect)
       .def("can_tile", &Rect::CanTile)
       .def("can_tile_x", &Rect::CanTileX)
       .def("can_tile_y", &Rect::CanTileY)
       .def("is_alt_group", &Rect::IsAltGroup)
       ;
    
    nb::class_<WeightConfig>(m, "WeightConfig")
       .def(nb::init<>())
       .def_prop_rw("pow_cardinality",
                    [](WeightConfig &t) { return t.pow_cardinality; },
                    [](WeightConfig &t, float v) { t.pow_cardinality = v; }
                )
    //    .def_prop_rw("pow_scale_diff",
    //                 [](WeightConfig &t) { return t.pow_scale_diff; },
    //                 [](WeightConfig &t, float v) { t.pow_scale_diff = v; }
    //             )
       .def_prop_rw("weight_dot",
                    [](WeightConfig &t) { return t.weight_dot; },
                    [](WeightConfig &t, float v) { t.weight_dot = v; }
                )
       .def_prop_rw("weight_scale",
                    [](WeightConfig &t) { return t.weight_scale; },
                    [](WeightConfig &t, float v) { t.weight_scale = v; }
                )
       .def_prop_rw("weight_tiling",
                    [](WeightConfig &t) { return t.weight_tiling; },
                    [](WeightConfig &t, float v) { t.weight_tiling = v; }
                )
       .def_prop_rw("error_margin",
                    [](WeightConfig &t) { return t.error_margin; },
                    [](WeightConfig &t, float v) { t.error_margin = v; }
                )
       ;
    
    nb::class_<RectFitResult>(m, "RectFitResult")
       .def(nb::init<int, bool>(), nb::arg("rect_idx"), nb::arg("rotated"))
       .def_prop_rw("rect_idx",
                    [](RectFitResult &t) { return t.rect_idx; },
                    [](RectFitResult &t, int v) { t.rect_idx = v; }
                )
       .def_prop_rw("tiling",
                    [](RectFitResult &t) -> auto& { return t.tiling; },
                    [](RectFitResult &t, Vec2f v) { t.tiling = v; }
                )
       .def_prop_rw("rotated",
                    [](RectFitResult &t) { return t.rotated; },
                    [](RectFitResult &t, bool v) { t.rotated = v; }
                )
       .def_prop_rw("score",
                    [](RectFitResult &t) { return t.score; },
                    [](RectFitResult &t, float v) { t.score = v; }
                )
       ;

    nb::class_<RectFile>(m, "RectFile")
       .def(nb::init<uint8_t, Vec2i, std::vector<HotSpot::Rect>>(), nb::arg("version"), nb::arg("tex_size"), nb::arg("rects"))
       .def_prop_rw("flags",
                    [](RectFile &t) { return t.flags; },
                    [](RectFile &t, uint8_t v) { t.flags = v; }
                )
       .def_prop_ro("tex_size",
                    [](RectFile &t) -> auto& { return t.tex_size; }
                )
       .def_prop_ro("rects",
                    [](RectFile &t) -> auto& { return t.rects; }
                )
       ;
}
