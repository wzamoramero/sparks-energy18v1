<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>

        <!-- Import Consumption Wizard Form -->
        <record id="view_import_consumption_wizard_form" model="ir.ui.view">
            <field name="name">sparks.import.consumption.wizard.form</field>
            <field name="model">sparks.import.consumption.wizard</field>
            <field name="arch" type="xml">
                <form string="Import Monthly Consumption Data">
                    <group invisible="state != 'upload'">
                        <group string="File Upload">
                            <field name="quotation_id" readonly="1"/>
                            <field name="import_file" filename="filename"/>
                            <field name="filename" invisible="1"/>
                            <field name="file_type"/>
                            <field name="has_header"/>
                        </group>
                        <group string="Column Configuration">
                            <field name="month_column"/>
                            <field name="consumption_column"/>
                            <field name="cost_column"/>
                        </group>
                    </group>

                    <group invisible="state != 'preview'">
                        <group string="Data Preview" colspan="2">
                            <field name="preview_data" nolabel="1" readonly="1" 
                                   widget="text" style="font-family: monospace;"/>
                        </group>
                    </group>

                    <group invisible="state != 'done'">
                        <div class="alert alert-success" role="alert">
                            <h4>Import Completed Successfully!</h4>
                            <p>The monthly consumption data has been imported and is now available in your quotation.</p>
                        </div>
                    </group>

                    <footer>
                        <button string="Preview Data" 
                                name="action_preview" 
                                type="object" 
                                class="btn-primary"
                                invisible="state != 'upload'"/>
                        
                        <button string="Back" 
                                name="action_back_to_upload" 
                                type="object" 
                                invisible="state != 'preview'"/>
                        
                        <button string="Import Data" 
                                name="action_import" 
                                type="object" 
                                class="btn-primary"
                                invisible="state != 'preview'"/>
                        
                        <button string="Close" 
                                name="action_close" 
                                type="object" 
                                class="btn-primary"
                                invisible="state != 'done'"/>
                        
                        <button string="Cancel" 
                                class="btn-secondary" 
                                special="cancel"/>
                    </footer>
                </form>
            </field>
        </record>

        <!-- Action for Import Wizard -->
        <record id="action_import_consumption_wizard" model="ir.actions.act_window">
            <field name="name">Import Consumption Data</field>
            <field name="res_model">sparks.import.consumption.wizard</field>
            <field name="view_mode">form</field>
            <field name="target">new</field>
        </record>

    </data>
</odoo>