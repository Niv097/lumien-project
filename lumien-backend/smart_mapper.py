"""
SmartMapper - Dynamic Excel Sheet & Column Discovery Engine for LUMIEN

Analyzes ANY Excel file and intelligently maps sheets and columns
to LUMIEN's data model, regardless of naming conventions used.
"""

import re
import pandas as pd
from collections import OrderedDict


class SmartMapper:
    """
    Analyzes an Excel workbook and dynamically maps:
    1. Sheet names -> Entity types (Banks, Users, Cases, etc.)
    2. Column names -> Canonical field names expected by the ingestion pipeline

    Ambiguity rule: First match wins.
    """

    # --- Sheet Discovery Patterns (most specific first) ---
    SHEET_PATTERNS = [
        ('readme',           ['readme']),
        ('status_codes',     ['statuscode', 'metastatus', 'codelookup']),
        ('scenarios',        ['scenario']),
        ('txn_details',      ['txndetail', 'transactiondetail']),
        ('status_responses', ['statusupdateresponse', 'statusresponse']),
        ('status_updates',   ['statusupdaterequest', 'statusrequest']),
        ('fraud_reports',    ['fraudreport', 'inboundfraud', 'inbound']),
        ('incidents',        ['incident']),
        ('hold_actions',     ['holdaction', 'bankhold']),
        ('timeline',         ['timeline']),
        ('workflow',         ['workflow']),
        ('branches',         ['branch']),
        ('users',            ['user', 'employee', 'staff', 'personnel']),
        ('banks',            ['bankmaster', 'banklist', 'bankdetail']),
    ]

    SHEET_FALLBACK = [
        ('fraud_reports', ['fraud', 'complaint', 'report', 'case']),
        ('incidents',     ['transaction', 'txn']),
        ('hold_actions',  ['hold', 'freeze', 'lien', 'block']),
        ('status_updates',['statusupdate']),
        ('banks',         ['bank', 'institution', 'lender', 'financial']),
        ('branches',      ['office', 'location']),
        ('users',         ['login', 'operator']),
        ('timeline',      ['step', 'stage']),
        ('status_codes',  ['lookup']),
    ]

    # --- Per-Entity Column Alias Maps ---
    ENTITY_COLUMNS = {
        'banks': OrderedDict([
            ('bank_code',         ['bank_code', 'code', 'bankcode', 'bank_id', 'institution_code', 'fi_code', 'short_code']),
            ('bank_name',         ['bank_name', 'name', 'bankname', 'institution_name', 'fi_name', 'bank_title', 'bank']),
            ('ifsc_prefix',       ['ifsc_prefix', 'ifsc', 'ifsc_code', 'ifscprefix', 'ifsccode']),
            ('integration_model', ['integration_model', 'model', 'integration', 'integrationmodel']),
            ('sla_hours',         ['sla_hours', 'sla', 'hours', 'response_hours', 'tat_hours', 'tat']),
        ]),
        'branches': OrderedDict([
            ('branch_id',   ['branch_id', 'branch_code', 'branchid', 'branchcode', 'office_id', 'id']),
            ('branch_name', ['branch_name', 'branchname', 'office_name', 'name']),
            ('ifsc_prefix', ['ifsc_prefix', 'ifsc', 'ifsc_code', 'ifscprefix', 'ifsccode']),
            ('district',    ['district', 'city', 'location', 'town']),
            ('state',       ['state', 'province', 'region']),
        ]),
        'users': OrderedDict([
            ('user_id',    ['user_id', 'userid', 'username', 'user_name', 'login_id', 'emp_id', 'employee_id', 'id']),
            ('full_name',  ['full_name', 'fullname', 'employee_name', 'display_name', 'name']),
            ('role',       ['role', 'user_role', 'designation', 'position', 'type']),
            ('branch_id',  ['branch_id', 'branchid', 'branch', 'office_id']),
            ('email',      ['email', 'email_id', 'mail', 'email_address']),
            ('mobile',     ['mobile', 'phone', 'contact', 'mobile_number', 'phone_number', 'mobile_no']),
        ]),
        'fraud_reports': OrderedDict([
            ('acknowledgement_no',      ['acknowledgement_no', 'ack_no', 'ack_number', 'complaint_no', 'complaint_id', 'reference_no', 'ref_no', 'case_no', 'case_id', 'ack']),
            ('sub_category',            ['sub_category', 'subcategory', 'category', 'fraud_type', 'type']),
            ('requestor',               ['requestor', 'requester', 'source', 'origin']),
            ('payer_bank',              ['payer_bank', 'payerbank', 'victim_bank', 'sender_bank', 'bank_name', 'bank']),
            ('payer_bank_code',         ['payer_bank_code', 'payerbankcode', 'victim_bank_code', 'bank_code']),
            ('mode_of_payment',         ['mode_of_payment', 'payment_mode', 'mode', 'channel', 'payment_channel']),
            ('payer_mobile_number',     ['payer_mobile_number', 'payer_mobile', 'victim_mobile', 'mobile', 'phone']),
            ('payer_account_number',    ['payer_account_number', 'payer_account', 'victim_account', 'account_number', 'account_no', 'account']),
            ('state',                   ['state', 'victim_state', 'payer_state']),
            ('district',                ['district', 'victim_district', 'payer_district', 'city']),
            ('transaction_type',        ['transaction_type', 'txn_type']),
            ('wallet',                  ['wallet', 'ewallet']),
            ('received_at',             ['received_at', 'received_date', 'date', 'created_at', 'report_date']),
            ('incident_count',          ['incident_count', 'count', 'num_incidents', 'total_incidents']),
            ('total_disputed_amount',   ['total_disputed_amount', 'total_amount', 'disputed_amount', 'amount']),
            ('bank_ack_response_code',  ['bank_ack_response_code', 'response_code', 'ack_response_code']),
            ('bank_job_id',             ['bank_job_id', 'job_id', 'jobid']),
            ('calc_total_disputed_amount', ['calc_total_disputed_amount', 'calculated_amount']),
            ('amount_match_flag',       ['amount_match_flag', 'match_flag']),
        ]),
        'incidents': OrderedDict([
            ('acknowledgement_no', ['acknowledgement_no', 'ack_no', 'complaint_no', 'complaint_id', 'ref_no', 'case_id']),
            ('incident_id',        ['incident_id', 'txn_id', 'transaction_id', 'id']),
            ('sub_category',       ['sub_category', 'subcategory', 'category', 'fraud_type']),
            ('amount',             ['amount', 'txn_amount', 'transaction_amount', 'value']),
            ('rrn',                ['rrn', 'reference', 'utr', 'reference_number']),
            ('transaction_date',   ['transaction_date', 'txn_date', 'date']),
            ('transaction_time',   ['transaction_time', 'txn_time', 'time']),
            ('disputed_amount',    ['disputed_amount', 'dispute_amount']),
            ('layer',              ['layer', 'level', 'hop', 'chain_layer']),
            ('payee_bank',         ['payee_bank', 'beneficiary_bank', 'receiver_bank']),
            ('payee_bank_code',    ['payee_bank_code', 'beneficiary_bank_code']),
            ('payee_ifsc_code',    ['payee_ifsc_code', 'beneficiary_ifsc', 'payee_ifsc']),
            ('payee_account_number', ['payee_account_number', 'beneficiary_account', 'receiver_account', 'payee_account']),
        ]),
        'workflow': OrderedDict([
            ('case_id',            ['case_id', 'caseid', 'case_no']),
            ('acknowledgement_no', ['acknowledgement_no', 'ack_no', 'complaint_no', 'ref_no']),
            ('job_id',             ['job_id', 'jobid', 'job_no']),
            ('created_at',         ['created_at', 'creation_date', 'create_date', 'date_created', 'date']),
            ('assigned_queue',     ['assigned_queue', 'queue', 'assignment_queue']),
            ('assigned_branch_id', ['assigned_branch_id', 'branch_id', 'branchid', 'assigned_branch']),
            ('priority',           ['priority', 'urgency', 'severity']),
            ('current_state',      ['current_state', 'status', 'state', 'case_status']),
            ('scenario',           ['scenario', 'case_scenario', 'fraud_scenario']),
            ('remarks',            ['remarks', 'comment', 'notes', 'description']),
            ('status',             ['status', 'workflow_status']),
        ]),
        'hold_actions': OrderedDict([
            ('action_id',          ['action_id', 'id']),
            ('case_id',            ['case_id', 'caseid']),
            ('acknowledgement_no', ['acknowledgement_no', 'ack_no', 'ref_no']),
            ('incident_id',        ['incident_id', 'txn_id']),
            ('action_type',        ['action_type', 'type', 'hold_type']),
            ('action_time',        ['action_time', 'hold_time', 'executed_at', 'created_at', 'date']),
            ('requested_amount',   ['requested_amount', 'request_amount', 'expected_amount']),
            ('action_amount',      ['action_amount', 'actual_amount']),
            ('held_amount',        ['held_amount', 'frozen_amount', 'hold_amount', 'amount']),
            ('hold_reference',     ['hold_reference', 'reference', 'hold_ref']),
            ('negative_lien_flag', ['negative_lien_flag', 'lien_flag', 'negative_lien']),
            ('outcome',            ['outcome', 'result', 'action_result']),
            ('remarks',            ['remarks', 'comment', 'notes']),
        ]),
        'status_updates': OrderedDict([
            ('request_id',          ['request_id', 'req_id']),
            ('acknowledgement_no',  ['acknowledgement_no', 'ack_no', 'ref_no']),
            ('job_id',              ['job_id', 'jobid']),
            ('sent_at',             ['sent_at', 'sent_date', 'send_date', 'date']),
            ('content_type',        ['content_type', 'content']),
            ('authorization_type',  ['authorization_type', 'auth_type']),
            ('payload_encrypted',   ['payload_encrypted', 'encrypted_payload', 'payload']),
            ('transaction_count',   ['transaction_count', 'txn_count', 'count']),
        ]),
        'txn_details': OrderedDict([
            ('request_id',              ['request_id', 'req_id']),
            ('acknowledgement_no',      ['acknowledgement_no', 'ack_no', 'ref_no']),
            ('job_id',                  ['job_id', 'jobid']),
            ('incident_id',             ['incident_id', 'txn_id']),
            ('root_rrn_transaction_id', ['root_rrn_transaction_id', 'root_rrn']),
            ('root_bankid',             ['root_bankid', 'root_bank_id', 'root_bank']),
            ('root_account_number',     ['root_account_number', 'root_account']),
            ('amount',                  ['amount', 'txn_amount']),
            ('transaction_datetime',    ['transaction_datetime', 'txn_datetime', 'date']),
            ('disputed_amount',         ['disputed_amount', 'dispute_amount']),
            ('status_code',             ['status_code', 'status']),
            ('remarks',                 ['remarks', 'comment', 'notes']),
            ('phone_number',            ['phone_number', 'phone', 'mobile']),
            ('pan_number',              ['pan_number', 'pan']),
            ('email',                   ['email', 'mail']),
            ('root_ifsc_code',          ['root_ifsc_code', 'root_ifsc']),
            ('root_effective_balance',  ['root_effective_balance', 'effective_balance', 'balance']),
            ('negative_lien_flag',      ['negative_lien_flag', 'lien_flag']),
            ('hold_reference',          ['hold_reference', 'hold_ref']),
            ('held_amount',             ['held_amount', 'hold_amount']),
        ]),
        'status_responses': OrderedDict([
            ('request_id',        ['request_id', 'req_id']),
            ('i4c_response_code', ['i4c_response_code', 'response_code']),
            ('i4c_message',       ['i4c_message', 'response_message', 'message']),
            ('received_at',       ['received_at', 'received_date', 'date']),
            ('error_flag',        ['error_flag', 'error', 'is_error']),
        ]),
        'timeline': OrderedDict([
            ('case_id',            ['case_id', 'caseid']),
            ('acknowledgement_no', ['acknowledgement_no', 'ack_no', 'ref_no']),
            ('job_id',             ['job_id', 'jobid']),
            ('step_no',            ['step_no', 'step_number', 'sequence', 'seq_no', 'order']),
            ('step_name',          ['step_name', 'step', 'activity', 'action', 'name']),
            ('actor',              ['actor', 'performed_by', 'user', 'executor']),
            ('start_time',         ['start_time', 'start', 'begin_time', 'started_at']),
            ('end_time',           ['end_time', 'end', 'finish_time', 'ended_at', 'completed_at']),
            ('step_status',        ['step_status', 'status', 'result']),
            ('sla_target_minutes', ['sla_target_minutes', 'sla_target', 'target_minutes']),
            ('actual_minutes',     ['actual_minutes', 'actual_time', 'duration']),
            ('sla_breached',       ['sla_breached', 'breached', 'is_breached']),
        ]),
        'status_codes': OrderedDict([
            ('status_code',       ['status_code', 'code']),
            ('status_label',      ['status_label', 'label', 'name']),
            ('meaning',           ['meaning', 'description', 'definition']),
            ('owner',             ['owner', 'owned_by', 'responsible']),
            ('demo_example_usage',['demo_example_usage', 'example', 'usage']),
        ]),
        'scenarios': OrderedDict([
            ('scenario',    ['scenario', 'name', 'title']),
            ('description', ['description', 'desc', 'detail', 'details']),
        ]),
        'readme': OrderedDict([]),
    }

    def __init__(self, xl):
        self.xl = xl
        self.sheet_names = xl.sheet_names
        self.sheet_map = {}  # entity_type -> actual sheet name
        self._discover_sheets()

    @staticmethod
    def _normalize(s):
        """Remove all non-alphanumeric chars and lowercase"""
        return re.sub(r'[^a-z0-9]', '', str(s).lower())

    def _discover_sheets(self):
        """Match each entity type to the best sheet. First match wins."""
        claimed = set()

        # Phase 1: specific patterns
        for entity_type, keywords in self.SHEET_PATTERNS:
            if entity_type in self.sheet_map:
                continue
            for sheet in self.sheet_names:
                if sheet in claimed:
                    continue
                norm = self._normalize(sheet)
                for kw in keywords:
                    if kw in norm:
                        self.sheet_map[entity_type] = sheet
                        claimed.add(sheet)
                        break
                if entity_type in self.sheet_map:
                    break

        # Phase 2: fallback patterns for unclaimed entities
        for entity_type, keywords in self.SHEET_FALLBACK:
            if entity_type in self.sheet_map:
                continue
            for sheet in self.sheet_names:
                if sheet in claimed:
                    continue
                norm = self._normalize(sheet)
                for kw in keywords:
                    if kw in norm:
                        self.sheet_map[entity_type] = sheet
                        claimed.add(sheet)
                        break
                if entity_type in self.sheet_map:
                    break

        # Log results
        print("\n" + "=" * 60)
        print("SMART MAPPER - Sheet Discovery Results")
        print("=" * 60)
        for entity, sheet in self.sheet_map.items():
            print(f"  {entity:20s} -> {sheet}")
        unclaimed_sheets = [s for s in self.sheet_names if s not in claimed]
        if unclaimed_sheets:
            print(f"  Unclaimed sheets: {unclaimed_sheets}")
        unmatched = [e for e, _ in self.SHEET_PATTERNS if e not in self.sheet_map]
        if unmatched:
            print(f"  Unmatched entities: {unmatched}")
        print("=" * 60 + "\n")

    def load_sheet(self, entity_type):
        """Load and normalize a sheet for the given entity type."""
        sheet_name = self.sheet_map.get(entity_type)
        if not sheet_name:
            return pd.DataFrame()
        df = self.xl.parse(sheet_name)
        return self._normalize_columns(df, entity_type)

    def has_sheet(self, entity_type):
        """Check if a sheet was found for the given entity type."""
        return entity_type in self.sheet_map

    def _normalize_columns(self, df, entity_type):
        """Rename columns to canonical names based on fuzzy matching."""
        aliases = self.ENTITY_COLUMNS.get(entity_type, {})
        if not aliases:
            return df

        # Build normalized -> actual column mapping
        norm_to_actual = {}
        for col in df.columns:
            norm = self._normalize(col)
            if norm not in norm_to_actual:
                norm_to_actual[norm] = col

        rename_map = {}
        claimed_actuals = set()

        for canonical, alias_list in aliases.items():
            # If canonical already exists as a column, skip
            if canonical in df.columns:
                continue

            for alias in alias_list:
                norm_alias = self._normalize(alias)
                if norm_alias in norm_to_actual:
                    actual_col = norm_to_actual[norm_alias]
                    if actual_col not in claimed_actuals:
                        rename_map[actual_col] = canonical
                        claimed_actuals.add(actual_col)
                        break

        if rename_map:
            print(f"  [{entity_type}] Column mapping: {rename_map}")
            df = df.rename(columns=rename_map)

        # Auto-generate missing critical columns
        df = self._apply_smart_defaults(df, entity_type)
        return df

    def _apply_smart_defaults(self, df, entity_type):
        """Auto-generate missing critical columns from available data."""
        if entity_type == 'banks':
            if 'bank_code' not in df.columns and 'bank_name' in df.columns:
                df['bank_code'] = df['bank_name'].apply(
                    lambda x: re.sub(r'[^A-Z0-9]', '', str(x).upper())[:6] if pd.notna(x) else 'UNK'
                )
                print(f"  [banks] Auto-generated 'bank_code' from 'bank_name'")
            if 'ifsc_prefix' not in df.columns and 'bank_code' in df.columns:
                df['ifsc_prefix'] = df['bank_code'].apply(
                    lambda x: str(x).upper()[:4] if pd.notna(x) else ''
                )
                print(f"  [banks] Auto-generated 'ifsc_prefix' from 'bank_code'")

        elif entity_type == 'users':
            if 'user_id' not in df.columns and 'email' in df.columns:
                df['user_id'] = df['email'].apply(
                    lambda x: str(x).split('@')[0] if pd.notna(x) else ''
                )
                print(f"  [users] Auto-generated 'user_id' from 'email'")
            elif 'user_id' not in df.columns and 'full_name' in df.columns:
                df['user_id'] = df['full_name'].apply(
                    lambda x: re.sub(r'[^a-z0-9]', '', str(x).lower())[:20] if pd.notna(x) else ''
                )
                print(f"  [users] Auto-generated 'user_id' from 'full_name'")

        elif entity_type == 'fraud_reports':
            if 'acknowledgement_no' not in df.columns:
                # Generate sequential IDs
                df['acknowledgement_no'] = [str(10000000 + i) for i in range(len(df))]
                print(f"  [fraud_reports] Auto-generated 'acknowledgement_no' (sequential)")

        elif entity_type == 'workflow':
            if 'case_id' not in df.columns and 'acknowledgement_no' in df.columns:
                df['case_id'] = df['acknowledgement_no'].apply(
                    lambda x: f"CASE-{str(x).strip()}" if pd.notna(x) else ''
                )
                print(f"  [workflow] Auto-generated 'case_id' from 'acknowledgement_no'")

        return df

    def extract_banks_from_cases(self, df_cases):
        """
        If no dedicated banks sheet exists, extract unique bank names
        from the fraud_reports/cases data and create a synthetic banks DataFrame.
        """
        bank_col = None
        for col_name in ['payer_bank', 'bank_name', 'bank', 'victim_bank', 'sender_bank']:
            if col_name in df_cases.columns:
                bank_col = col_name
                break

        if not bank_col:
            # Try normalized matching
            for col in df_cases.columns:
                norm = self._normalize(col)
                if 'bank' in norm and 'code' not in norm:
                    bank_col = col
                    break

        if not bank_col:
            return pd.DataFrame()

        unique_banks = df_cases[bank_col].dropna().unique()
        rows = []
        for i, bname in enumerate(unique_banks):
            bname = str(bname).strip()
            if not bname:
                continue
            code = re.sub(r'[^A-Z0-9]', '', bname.upper())[:6]
            rows.append({
                'bank_name': bname,
                'bank_code': code,
                'ifsc_prefix': code[:4],
                'integration_model': 'MANUAL',
                'sla_hours': 24,
            })

        print(f"  [auto] Extracted {len(rows)} banks from cases column '{bank_col}'")
        return pd.DataFrame(rows)

    def generate_default_branches(self, bank_names_codes):
        """Generate a default HQ branch for each bank when no branches sheet exists."""
        rows = []
        for bname, bcode in bank_names_codes:
            rows.append({
                'branch_id': f'BR-{bcode}-HQ',
                'branch_name': f'{bname} - Head Office',
                'ifsc_prefix': bcode[:4],
                'district': 'Head Office',
                'state': 'India',
            })
        print(f"  [auto] Generated {len(rows)} default HQ branches")
        return pd.DataFrame(rows)

    def generate_default_users(self, bank_names_codes):
        """Generate default admin + bank users when no users sheet exists."""
        rows = [
            {'user_id': 'admin', 'full_name': 'Platform Admin', 'role': 'ADMIN', 'branch_id': '', 'email': 'admin@lumien.local'},
        ]
        for bname, bcode in bank_names_codes:
            rows.append({
                'user_id': f'{bcode.lower()}_maker',
                'full_name': f'{bname} Maker',
                'role': 'MAKER',
                'branch_id': f'BR-{bcode}-HQ',
                'email': f'{bcode.lower()}_maker@lumien.local',
            })
        print(f"  [auto] Generated {len(rows)} default users")
        return pd.DataFrame(rows)
