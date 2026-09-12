#!/usr/bin/env python3
"""Compatibility entry point: audit the NEW measurement and furniture PNGs."""
from audit_measured import model, checks, render_plans, render_iso

if __name__ == '__main__':
    model.build_scene()
    checks()
    render_plans()
    render_iso()
    print('Updated comparison.html, plan-overlay.png, model-top.png and model-isometric.png')
