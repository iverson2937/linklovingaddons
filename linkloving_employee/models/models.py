# -*- coding: utf-8 -*-

from odoo import models, fields, api
from string import lower
import re
from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


class LinkLovingEmployee(models.Model):
    _inherit = 'hr.employee'

    is_view_more_msg = fields.Boolean(u'是否显示更多信息', compute='_compute_is_view_more_msg')

    is_self = fields.Boolean(u'是不是本人', compute='_compute_is_self')

    is_manager = fields.Boolean(u'是不是经理', compute='_compute_is_manager')

    # 公开信息
    employee_state = fields.Selection([('draft', u'草稿'), ('submitted_ing', u'已提交'), ('official', u'正式')],
                                      string=u'员工状态', track_visibility='onchange',
                                      default='draft')
    english_name = fields.Char(u'英文名称')
    work_card = fields.Char(u'工号')

    # 个人信息
    nation = fields.Many2one('hr.nation', u'民族')
    address_home_two = fields.Char(u'家庭住址')
    now_address_home = fields.Char(u'现住址')
    emergency_contact_name = fields.Char(u'姓名')
    emergency_contact_relation = fields.Char(u'关系')
    emergency_contact_way = fields.Char(u'联系方式')
    work_experience_ids = fields.One2many('hr.work.experience', 'employee_work_id', string=u'工作经历')
    education_experience_ids = fields.One2many('hr.education.experience', 'employee_education_id', string=u'教育经历')
    identification_A = fields.Binary(u'身份证正面')
    identification_B = fields.Binary(u'身份证反面')
    bank_card = fields.Binary(u'银行卡')
    bank_card_num = fields.Char(u'银行卡卡号')
    bank_card_opening_bank = fields.Char(u'银行卡开户行')
    certificate_image_ids = fields.Many2many('ir.attachment', string=u'证书')

    # hr 设置
    entry_date = fields.Date(u'入职日期')

    probation_date = fields.Char(u'试用期时间')

    probation_begin_date = fields.Datetime(u'试用期开始日期')
    probation_end_date = fields.Datetime(u'试用期结束日期')
    mining_productivity = fields.Selection(
        [('practice_work', u'实习'), ('dispatch_work', u'派遣'), ('try_out_work', u'试用'), ('fixed_work', u'正式'),
         ('leaving_work', u'离职')], string=u'用工形式')

    contract_begin_date = fields.Datetime(string=u'合同签订')
    contract_end_date = fields.Datetime(string=u'合同终止')
    accumulation_fund = fields.Selection(
        [('class_a', u'甲类'), ('class_b', u'乙类'), ('null', u'无')], string=u'交金类别')
    insurance_type = fields.Many2one('hr.insurance', string=u'保险类别')
    buy_balance = fields.Float(u'申购余额')
    is_create_account = fields.Boolean(u'相关用户', default=True)
    probation_period = fields.Selection(
        [('nothing', u'无'), ('half_month', u'半个月'), ('one_month', u'一个月'), ('two_month', u'两个月'),
         ('three_month', u'三个月')],
        string=u'试用期')

    # 重写原生字段
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ])
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widower', '丧偶'),
    ], string='Marital Status')

    card_num = fields.Char(string=u'工牌')

    def get_employee_child(self, data):

        em_data_all = self.env['hr.employee']

        for em_one in data:
            em_data_all += em_one.child_ids
            if em_one.child_ids:
                for em_two in em_one.child_ids:
                    em_data_all += self.get_employee_child(em_two)

        return em_data_all

    # def get_employee_child11111(self, data):
    #
    #     em_data_all = self.env['hr.employee']
    #
    #     def get_employee_child_inner(data, em):
    #         for em_one in data.child_ids:
    #             em += data.child_ids
    #             get_employee_child_inner(em_one, em)
    #
    #     get_employee_child_inner(data, em_data_all)
    #     return em_data_all

    # def compute_is_view_more_msg11(self):
    #
    #     # department_manager = self.env.user.employee_ids.department_id.manager_id  # 得到登录用户所在部门 的经理
    #
    #     if self.env.ref('hr.group_hr_manager').id in self.env.user.groups_id.ids:
    #         for emp_one in self:
    #             emp_one.is_view_more_msg = True
    #     else:
    #         for emp_one in self:
    #             if emp_one in self.env.user.employee_ids + self.env.user.employee_ids.child_ids:
    #                 emp_one.is_view_more_msg = True


    def _compute_is_self(self):
        for emp_one in self:
            if emp_one in self.env.user.employee_ids:
                emp_one.is_self = True

    def _compute_is_manager(self):
        for emp_one in self:
            if self.env.ref('hr.group_hr_manager').id in self.env.user.groups_id.ids:
                emp_one.is_manager = True

    def _compute_is_view_more_msg(self):

        if self.env.ref('hr.group_hr_manager').id in self.env.user.groups_id.ids:
            for emp_one in self:
                emp_one.is_view_more_msg = True
        else:

            em_data_all = self.get_employee_child(self.env.user.employee_ids)

            for emp_one in self:
                if emp_one in self.env.user.employee_ids + em_data_all:
                    emp_one.is_view_more_msg = True

    # 验证
    def btn_click_verification_employee(self):
        if self.employee_state in ('submitted_ing', 'draft'):
            self.employee_state = 'official'
        else:
            raise UserError('已经是正式')

    # 提交
    def btn_click_submit_employee(self):
        if self.employee_state == 'draft':
            self.employee_state = 'submitted_ing'
        else:
            raise UserError('不是草稿状态,不能提交')

    # 正式 退回 草稿
    def btn_click_verification_draft_employee(self):
        if self.employee_state != 'draft':
            self.employee_state = 'draft'
        else:
            raise UserError('不是正式状态，不能退回')

    # def btn_click_draft_verification_employee(self):
    #     if self.employee_state == 'draft':
    #         self.employee_state = 'official'
    #     else:
    #         raise UserError('不是正式状态，不能退回')

    def create_nation(self):
        name_data = "汉族、蒙古族、回族、藏族、维吾尔族、苗族、彝族、壮族、布依族、朝鲜族、满族、侗族、瑶族、白族、土家族、哈尼族、哈萨克族、傣族、黎族、僳僳族、佤族、畲族、高山族、拉祜族、水族、东乡族、纳西族、景颇族、柯尔克孜族、土族、达斡尔族、仫佬族、羌族、布朗族、撒拉族、毛南族、仡佬族、锡伯族、阿昌族、普米族、塔吉克族、怒族、乌孜别克族、俄罗斯族、鄂温克族、德昂族、保安族、裕固族、京族、塔塔尔族、独龙族、鄂伦春族、赫哲族、门巴族、珞巴族、基诺族"
        name_list = name_data.split('、')

        for name_one in name_list:
            self.env['hr.nation'].create({'name': name_one})

    def verification_email(self, vals):

        identification_one = vals.get('identification_id')
        email_one = vals.get('work_email')
        mobile_phone_one = vals.get('mobile_phone')
        entry_date_ver = vals.get('entry_date')

        if entry_date_ver:
            if datetime.strptime(entry_date_ver.split(' ')[0], '%Y-%m-%d') > datetime.now():
                raise UserError('入职日期不能大于今天')

        if mobile_phone_one:
            if not re.match(r'^1[358]\d{9}$', mobile_phone_one):
                raise UserError('办公手机 格式有问题 ：' + str(mobile_phone_one))

        if identification_one:
            if re.match(r'^([1-9]\d{5}[12]\d{3}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])\d{3}[0-9xX])$',
                        identification_one):
                id_one = self.env['hr.employee'].search(
                    [('identification_id', '=', identification_one.strip())])
                if id_one:
                    raise UserError('此身份证：' + str(identification_one) + '已存在')
            else:
                raise UserError('身份证 格式有问题 ：' + str(identification_one))

        if email_one:
            if re.match(r'^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$', email_one):
                em_one = self.env['hr.employee'].search([('work_email', '=', email_one.strip())])
                user_one = self.env['res.users'].search([('login', '=', email_one.strip())])
                if em_one or user_one:
                    raise UserError('此Email：' + str(email_one) + '已存在')
            else:
                raise UserError('Email 格式有问题 ：' + str(email_one))
                # # 查重
                # email_list = self.search([('work_email', '=', email_one.strip())])
                # if email_list:
                #     raise UserError('此Email：' + str(email_one) + '已存在，请再次输入')

    @api.model
    def create(self, vals):

        # 验证是否合法
        self.verification_email(vals)

        vals['probation_date'] = self.get_probation_date(vals.get("entry_date"), vals.get("probation_period"))

        vals['work_card'] = str(len(self.search([])) + 1).zfill(5) if self.search([]) else '00001'

        if vals.get('is_create_account'):
            # 创建用户--》个人客户 并关联到员工
            res = self.env['res.users'].create({'name': vals.get('name'), 'login': vals.get('work_email')})
            # 设定初始的密码
            pass_wizard = self.env['change.password.wizard'].create({})
            self.env['change.password.user'].create({
                'wizard_id': pass_wizard.id,
                'user_id': res.id,
                'new_passwd': '123456'
            })
            pass_wizard.change_password_button()
            # vals['is_create_account'] = False
            vals['user_id'] = res.id

        employee_data = super(LinkLovingEmployee, self).create(vals)
        return employee_data

    @api.multi
    def write(self, vals):
        # 验证是否合法
        self.verification_email(vals)
        # 获取 入职时间段
        # vals['probation_date'] = ''
        if vals.get('entry_date') and vals.get('probation_period'):
            vals['probation_date'] = self.get_probation_date(vals.get("entry_date"), vals.get("probation_period"))
        elif vals.get('entry_date') and self.probation_period:
            vals['probation_date'] = self.get_probation_date(vals.get("entry_date"), self.probation_period)
        elif 'probation_period' in vals and self.entry_date:
            vals['probation_date'] = self.get_probation_date(self.entry_date, vals.get("probation_period"))

        return super(LinkLovingEmployee, self).write(vals)

    def get_probation_date(self, def_entry_date, def_probation_period):

        if def_entry_date:
            entry_date_self = datetime.strptime(str(def_entry_date).split(' ')[0], '%Y-%m-%d')
            probation_end_date = False
            if def_probation_period == 'half_month':
                probation_end_date = relativedelta(days=+15)
            elif def_probation_period == 'one_month':
                probation_end_date = relativedelta(months=+1)
            elif def_probation_period == 'two_month':
                probation_end_date = relativedelta(months=+2)
            elif def_probation_period == 'three_month':
                probation_end_date = relativedelta(months=+3)

            data = def_entry_date + '~'
            if probation_end_date:
                return data + str(entry_date_self + probation_end_date - relativedelta(days=+1)).split(' ')[0]
            else:
                return ' '

    @api.onchange('probation_period')
    def onchange_probation_period(self):
        # if self.entry_date:
        #     entry_date_self = datetime.strptime(str(self.entry_date).split(' ')[0], '%Y-%m-%d')
        #     probation_end_date = ' '
        #     if self.probation_period == 'half_month':
        #         probation_end_date = relativedelta(days=+15)
        #     elif self.probation_period == 'one_month':
        #         probation_end_date = relativedelta(months=+1)
        #     elif self.probation_period == 'two_month':
        #         probation_end_date = relativedelta(months=+2)
        #     elif self.probation_period == 'three_month':
        #         probation_end_date = relativedelta(months=+3)
        #
        #     self.probation_date = self.entry_date + '-' + \
        #                           str(entry_date_self + probation_end_date - relativedelta(days=+1)).split(' ')[0]
        self.probation_date = self.get_probation_date(self.entry_date, self.probation_period)


class LinkLovingEmployeeWorkExperience(models.Model):
    _name = 'hr.work.experience'

    name = fields.Char(u'公司', required=True)
    department = fields.Char(u'部门', required=True)
    position = fields.Char(u'职位', required=True)
    entry_time = fields.Date(u'入职时间', required=True)
    Leaving_time = fields.Date(u'离职时间')
    employee_work_id = fields.Many2one('hr.employee')


class LinkLovingEmployeeEducationExperience(models.Model):
    _name = 'hr.education.experience'

    name = fields.Char(u'学校', required=True)
    attainment = fields.Selection(
        [('fixed_work', u'高中'), ('temp_work', u'中专'), ('part_time_work', u'大专'), ('part_time_work', u'本科'),
         ('part_time_work', u'硕士'), ('part_time_work', u'MBA'), ('part_time_work', u'博士')], u'学历', required=True)
    major = fields.Char(u'专业', required=True)
    entry_time = fields.Date(u'入学时间', required=True)
    Leaving_time = fields.Date(u'毕业时间', required=True)
    employee_education_id = fields.Many2one('hr.employee')


class LinkLovingEmployeeNation(models.Model):
    _name = 'hr.nation'

    name = fields.Char(u'民族')


class LinkLovingEmployeeInsurance(models.Model):
    _name = 'hr.insurance'

    name = fields.Char(u'保险名称')
