"""Streamlit application for the interior estimator.

Run this script with ``streamlit run app.py`` after installing the
project with the ``[web]`` extra.  The app provides a simple form
to enter room dimensions, unit prices and the labour rate.  It then
displays the resulting estimate and offers a PDF download when
``reportlab`` is installed.
"""

from __future__ import annotations

import io
import streamlit as st

from interior_estimator.core import (
    RoomMeasurements,
    UnitPrices,
    create_estimate_for_room,
)


def main() -> None:
    st.set_page_config(page_title="Interior Estimator", layout="centered")
    st.title("🏠 内装工事 見積作成ツール")

    st.write(
        "部屋の寸法や単価を入力すると、クロス貼り替えや床仕上げ、巾木交換、"
        "既存材の処分費を含む見積書を自動計算します。"
    )

    with st.form("estimate_form"):
        st.subheader("📏 寸法")
        col1, col2 = st.columns(2)
        length = col1.number_input("長さ (m)", min_value=0.0, value=5.0)
        width = col2.number_input("幅 (m)", min_value=0.0, value=4.0)
        height = col1.number_input("高さ (m)", min_value=0.0, value=2.5)
        openings = col2.number_input("開口部合計面積 (m²)", min_value=0.0, value=0.0)

        st.subheader("💴 単価 (円)")
        prices = UnitPrices()
        cross_price = st.number_input("クロス (/m²)", min_value=0.0, value=float(prices.クロス))
        floor_price = st.number_input("床 (/m²)", min_value=0.0, value=float(prices.床))
        baseboard_price = st.number_input("巾木 (/m)", min_value=0.0, value=float(prices.巾木))
        disposal_price = st.number_input("処分費 (/m²)", min_value=0.0, value=float(prices.処分費))
        labour_rate = st.number_input(
            "人件費率 (材料費に対する割合)",
            min_value=0.0,
            max_value=1.0,
            value=float(prices.人件費率),
            step=0.05,
        )
        generate_button = st.form_submit_button("見積を作成")

    if generate_button:
        room = RoomMeasurements(length=length, width=width, height=height, openings_area=openings)
        prices.クロス = cross_price
        prices.床 = floor_price
        prices.巾木 = baseboard_price
        prices.処分費 = disposal_price
        prices.人件費率 = labour_rate

        estimate = create_estimate_for_room(room, prices)

        st.subheader("📄 見積書")
        # show text representation
        st.text(estimate.to_text())

        # Attempt to offer PDF download if reportlab is available
        try:
            # generate PDF in memory
            pdf_buffer = io.BytesIO()
            estimate.to_pdf("/dev/null")  # create to ensure dependencies; will raise if missing
        except RuntimeError:
            st.info("PDF出力には reportlab が必要です。'pip install reportlab' を行ってください。")
        else:
            # Now generate actual PDF into buffer
            try:
                # We can't write directly to /dev/null with BytesIO; need to call to_pdf with filelike
                # We implement a simple context manager to intercept the save
                estimate.to_pdf = estimate.to_pdf  # no-op to please linter
                from reportlab.pdfgen import canvas as rl_canvas

                # Build PDF using reportlab into memory
                pdf_buffer = io.BytesIO()
                c = rl_canvas.Canvas(pdf_buffer, pagesize=(595.27, 841.89))  # A4 points
                # Use original to_pdf logic from core to draw content
                # We'll manually call the Estimate.to_pdf implementation defined in core
                # by temporarily monkey patching canvas to our memory canvas.
                # Since the Estimate.to_pdf uses module-level canvas, we can call
                # directly by setting module variable if necessary.
                # Instead of patching, call again using our own file; we need to call
                # estimate.to_pdf but pass file path; easiest: create temp file and read. However,
                # here we rely on memory; we replicate the code here is heavy; instead we call
                # estimate.to_pdf with a temporary file and read contents.
                import tempfile

                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                    estimate.to_pdf(tmp.name)
                    tmp.seek(0)
                    pdf_buffer.write(tmp.read())
                pdf_buffer.seek(0)
            except Exception:
                st.error("PDFの生成中にエラーが発生しました。")
                pdf_buffer = None

            if pdf_buffer:
                st.download_button(
                    label="📥 PDFをダウンロード",
                    data=pdf_buffer,
                    file_name="estimate.pdf",
                    mime="application/pdf",
                )


if __name__ == "__main__":
    main()
