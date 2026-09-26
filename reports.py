import io
import csv
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, send_file
from models import db, Transaction, User
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/summary', methods=['GET'])
def get_monthly_report():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    # Income
    income_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'income',
        Transaction.date.startswith(month)
    ).all()
    total_income = sum(t.amount for t in income_txs)
    if total_income == 0 and user.monthly_income:
        total_income = user.monthly_income

    # Expenses
    expense_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()
    total_expenses = sum(t.amount for t in expense_txs)
    total_savings = max(total_income - total_expenses, 0)
    savings_rate = round((total_savings / total_income * 100), 1) if total_income > 0 else 0

    category_totals = {}
    for tx in expense_txs:
        category_totals[tx.category] = category_totals.get(tx.category, 0) + tx.amount

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    top_cat = sorted_categories[0] if sorted_categories else ('None', 0)

    category_list = []
    for cat, amt in sorted_categories:
        pct = round((amt / total_expenses * 100), 1) if total_expenses > 0 else 0
        category_list.append({
            'category': cat,
            'amount': amt,
            'percentage': pct
        })

    return jsonify({
        'user': {'name': user.name, 'email': user.email, 'currency': user.currency},
        'month': month,
        'summary': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'total_savings': total_savings,
            'savings_rate': savings_rate,
            'top_spending_category': {
                'name': top_cat[0],
                'amount': top_cat[1]
            }
        },
        'categories': category_list,
        'transaction_count': len(expense_txs) + len(income_txs)
    }), 200


@reports_bp.route('/download-csv', methods=['GET'])
def download_csv():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.date.startswith(month)
    ).order_by(Transaction.date.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Title & Metadata
    writer.writerow(["Personal Finance Advisor Bot - Monthly Financial Report"])
    writer.writerow([f"User: {user.name}", f"Period: {month}", f"Currency: {user.currency}"])
    writer.writerow([])

    # Header
    writer.writerow(["Date", "Description", "Category", "Type", f"Amount ({user.currency})"])

    total_income = 0
    total_expense = 0

    for t in txs:
        prefix = "+" if t.type == 'income' else "-"
        writer.writerow([
            t.date,
            t.description,
            t.category,
            t.type.capitalize(),
            f"{prefix}{t.amount:.2f}"
        ])
        if t.type == 'income':
            total_income += t.amount
        else:
            total_expense += t.amount

    writer.writerow([])
    writer.writerow(["Summary Overview"])
    writer.writerow(["Total Income", f"{total_income:.2f}"])
    writer.writerow(["Total Expenses", f"{total_expense:.2f}"])
    writer.writerow(["Net Savings", f"{(total_income - total_expense):.2f}"])
    rate = round(((total_income - total_expense) / total_income * 100), 1) if total_income > 0 else 0
    writer.writerow(["Savings Rate", f"{rate}%"])

    output.seek(0)
    filename = f"financial_report_{month}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@reports_bp.route('/download-pdf', methods=['GET'])
def download_pdf():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    income_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'income',
        Transaction.date.startswith(month)
    ).all()
    total_income = sum(t.amount for t in income_txs)
    if total_income == 0 and user.monthly_income:
        total_income = user.monthly_income

    expense_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).order_by(Transaction.date.asc()).all()

    total_expenses = sum(t.amount for t in expense_txs)
    total_savings = max(total_income - total_expenses, 0)
    savings_rate = round((total_savings / total_income * 100), 1) if total_income > 0 else 0

    # Build PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=18
    )
    heading2 = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=8
    )

    elements.append(Paragraph("Personal Finance Advisor Bot", title_style))
    elements.append(Paragraph(f"Monthly Financial Statement • Prepared for {user.name} • Month: {month}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Summary Table
    summary_data = [
        ["Financial Metric", "Amount (INR / ₹)", "Status / Ratio"],
        ["Total Income", f"₹{total_income:,.2f}", "100% of Inflow"],
        ["Total Expenses", f"₹{total_expenses:,.2f}", f"{round(total_expenses/total_income*100 if total_income > 0 else 0)}% of Income"],
        ["Net Savings", f"₹{total_savings:,.2f}", f"Savings Rate: {savings_rate}%"],
    ]
    summary_table = Table(summary_data, colWidths=[200, 160, 160])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#ECFDF5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))

    # Transactions List Table
    elements.append(Paragraph("Itemized Expense & Income Log", heading2))
    
    tx_table_data = [["Date", "Description", "Category", "Type", "Amount"]]
    # Combine income and expenses sorted by date
    all_month_txs = sorted(income_txs + expense_txs, key=lambda x: x.date)
    for t in all_month_txs[:30]:  # limit to fit nicely
        color_symbol = "+" if t.type == 'income' else "-"
        tx_table_data.append([
            t.date,
            t.description[:25],
            t.category,
            t.type.capitalize(),
            f"{color_symbol}₹{t.amount:,.2f}"
        ])

    tx_table = Table(tx_table_data, colWidths=[75, 175, 110, 70, 90])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(tx_table)

    doc.build(elements)
    buffer.seek(0)

    filename = f"financial_statement_{month}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
