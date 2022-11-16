from odoo import models, api, fields, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_ids = fields.Many2many('sale.order', string='sale references')

    def stock_picking_smart_button(self):
        self.ensure_one()
        return {
            'name': 'Sale Order',
            'domain': [('id', 'in', self.sale_ids.ids)],
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }

    def auto_merge_picking(self):
        move_obj = self.env['stock.move']
        partners = self.search(
            [('state', 'not in', ['done', 'cancel']), ('picking_type_code', '=', 'outgoing')]).mapped('partner_id')
        for partner in partners:
            picking_type_ids = self.search([('state', 'not in', ['done', 'cancel']), ('partner_id', '=', partner.id),
                                            ('picking_type_code', '=', 'outgoing')]).mapped('picking_type_id')
            for picking_type_id in picking_type_ids:
                picking_ids = self.search([('state', 'not in', ['done', 'cancel']), ('partner_id', '=', partner.id),
                                           ('picking_type_id', '=', picking_type_id.id)])
                if len(picking_ids) > 1:
                    total_origin = ""
                    custom_sale_list = []
                    new_picking_id = picking_ids[0].copy({'state':'draft'})
                    remaining_picking_ids = picking_ids.filtered(lambda pick: pick.id != picking_ids[0].id)
                    total_origin += picking_ids[0].origin + ", "
                    if picking_ids[0].sale_id:
                        custom_sale_list.append(picking_ids[0].sale_id.id)
                    picking_ids[0].action_cancel()
                    for remaining_picking_id in remaining_picking_ids:
                        total_origin += remaining_picking_id.origin + ", "
                        for move in remaining_picking_id.move_lines:
                            new_move = move_obj.create({
                                'name': move.name or '',
                                'product_id': move.product_id and move.product_id.id or False,
                                'product_uom_qty': move.product_qty,
                                'product_uom': move.product_uom and move.product_uom.id or False,
                                'date': move.date,
                                'date_deadline': move.date_deadline,
                                'location_id': move.location_id and move.location_id.id or False,
                                'location_dest_id': move.location_dest_id and move.location_dest_id.id or False,
                                'picking_id': new_picking_id.id,
                                'partner_id': move.partner_id and move.partner_id.id or False,
                                'move_dest_ids': [(6, 0, move.move_dest_ids.ids)] or False,
                                'state': move.state,
                                'company_id': move.company_id.id,
                                'price_unit': move.price_unit,
                                'group_id': move.group_id.id,
                                'picking_type_id': move.picking_type_id.id,
                                'sale_line_id': move.sale_line_id.id
                            })
                        if remaining_picking_id.sale_id:
                            custom_sale_list.append(remaining_picking_id.sale_id.id)
                            remaining_picking_id.sale_id.is_merged = True
                        remaining_picking_id.action_cancel()
                    new_picking_id.write({'origin': total_origin[:-2]})
                    new_picking_id.mapped('move_lines').sudo()._action_confirm()

                    new_picking_id.mapped('move_lines').sudo()._action_assign()

                    msg_body = "Auto Generated DO From : <b>{}</b>".format(picking_ids[0].name)
                    new_picking_id.message_post(body=msg_body)
                    new_picking_id.sale_ids = [(6, 0, custom_sale_list)]
