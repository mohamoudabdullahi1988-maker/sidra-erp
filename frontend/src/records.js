// The record lists of the interface, one entry per list key. The keys match LISTS in
// sidra_realestate/www/berjaya.py, which tells each user which lists they may read and create.
// Columns and detail fields are exact DocType field names: the REST API returns only the fields
// a user may read, and a field it leaves out is shown as "Unavailable".
//
// Field types: text | id | date | datetime | money | int | percent | check | status | file |
// longtext | user | link (with `to`, the list key of the linked record)

const DOC = { field: 'docstatus', label: 'State', type: 'docstatus' }

export const RECORDS = {
  units: {
    section: 'properties',
    title: 'Units',
    noun: 'units',
    doctype: 'Sidra Unit',
    path: '/properties',
    page: 'properties',
    form: true,
    status: { Available: 'completed', Reserved: 'current', 'Under Contract': 'current', Sold: 'muted', Blocked: 'blocked' },
    detail: {
      title: 'unit_code',
      subtitle: 'scheme',
      groups: [
        {
          title: 'Unit',
          fields: [
            { field: 'unit_code', label: 'Unit code' },
            { field: 'scheme', label: 'Scheme', type: 'link', to: 'schemes' },
            { field: 'company', label: 'Company' },
            { field: 'block', label: 'Block / phase' },
            { field: 'unit_type', label: 'Type' },
            { field: 'status', label: 'Status', type: 'status' },
            { field: 'cash_price', label: 'Cash price', type: 'money' },
            { field: 'title_deed_ref', label: 'Title deed reference' },
            { field: 'current_reservation', label: 'Current reservation', type: 'link', to: 'reservations' },
            { field: 'current_contract', label: 'Current contract', type: 'link', to: 'contracts' },
          ],
        },
        {
          title: 'Plot',
          fields: [
            { field: 'plot_fraction', label: 'Plot fraction' },
            { field: 'dimensions', label: 'Dimensions' },
            { field: 'area_sqm', label: 'Area (m²)', type: 'number' },
            { field: 'district', label: 'District' },
            { field: 'neighbourhood', label: 'Neighbourhood' },
            { field: 'land_parcel', label: 'Original land parcel' },
            { field: 'boundary_east', label: 'East' },
            { field: 'boundary_north', label: 'North' },
            { field: 'boundary_south', label: 'South' },
            { field: 'boundary_west', label: 'West' },
          ],
        },
        {
          title: 'House / off-plan',
          fields: [
            { field: 'offplan_status', label: 'Off-plan status' },
            { field: 'delivery_date', label: 'Estimated delivery', type: 'date' },
            { field: 'expansion_phase', label: 'Expansion phase' },
            { field: 'bedrooms', label: 'Bedrooms', type: 'int' },
            { field: 'floors', label: 'Floors', type: 'int' },
          ],
        },
      ],
      related: [
        { list: 'reservations', field: 'unit', title: 'Reservations' },
        { list: 'price_history', field: 'unit', title: 'Price history' },
      ],
    },
  },
  schemes: {
    section: 'properties',
    title: 'Schemes',
    noun: 'schemes',
    doctype: 'Sidra Scheme',
    path: '/properties/schemes',
    icon: 'lucide-map',
    form: true,
    company: true,
    orderBy: 'scheme_code asc',
    search: ['name', 'scheme_name', 'district'],
    searchLabel: 'Code, name or district',
    list: [
      { field: 'scheme_code', label: 'Code', type: 'id' },
      { field: 'scheme_name', label: 'Name' },
      { field: 'district', label: 'District' },
      { field: 'neighbourhood', label: 'Neighbourhood' },
      { field: 'company', label: 'Company' },
    ],
    detail: {
      title: 'scheme_name',
      subtitle: 'scheme_code',
      groups: [
        {
          title: 'Scheme',
          fields: [
            { field: 'scheme_code', label: 'Code' },
            { field: 'scheme_name', label: 'Name' },
            { field: 'company', label: 'Company' },
            { field: 'location', label: 'Location' },
            { field: 'district', label: 'District' },
            { field: 'neighbourhood', label: 'Neighbourhood' },
            { field: 'description', label: 'Description', type: 'longtext' },
          ],
        },
      ],
      related: [
        {
          list: 'units',
          field: 'scheme',
          title: 'Units',
          orderBy: 'unit_code asc',
          columns: [
            { field: 'unit_code', label: 'Unit', type: 'id' },
            { field: 'unit_type', label: 'Type' },
            { field: 'status', label: 'Status', type: 'status' },
            { field: 'cash_price', label: 'Cash price', type: 'money' },
          ],
        },
      ],
    },
  },
  price_history: {
    form: true,
    section: 'properties',
    title: 'Price history',
    noun: 'price changes',
    doctype: 'Sidra Unit Price History',
    path: '/properties/price-history',
    icon: 'lucide-tags',
    company: true,
    orderBy: 'effective_from desc, modified desc',
    search: ['name', 'unit', 'scheme'],
    searchLabel: 'Record, unit or scheme',
    list: [
      { field: 'name', label: 'Record', type: 'id' },
      { field: 'unit', label: 'Unit' },
      { field: 'scheme', label: 'Scheme' },
      { field: 'effective_from', label: 'Effective', type: 'date' },
      { field: 'previous_price', label: 'Previous price', type: 'money' },
      { field: 'price', label: 'New price', type: 'money' },
      DOC,
    ],
    extra: ['company'],
    detail: {
      subtitle: 'unit',
      groups: [
        {
          title: 'Price change',
          fields: [
            { field: 'unit', label: 'Unit' },
            { field: 'scheme', label: 'Scheme' },
            { field: 'company', label: 'Company' },
            { field: 'effective_from', label: 'Effective from', type: 'date' },
            { field: 'previous_price', label: 'Previous price', type: 'money' },
            { field: 'price', label: 'New price', type: 'money' },
            { field: 'reason', label: 'Reason', type: 'longtext' },
          ],
        },
      ],
    },
  },

  customers: {
    form: true,
    section: 'customers',
    title: 'Customers',
    noun: 'customers',
    doctype: 'Customer',
    path: '/customers',
    icon: 'lucide-users',
    orderBy: 'customer_name asc',
    search: ['name', 'customer_name', 'mobile_no'],
    searchLabel: 'Name or phone',
    list: [
      { field: 'customer_name', label: 'Customer', type: 'id' },
      { field: 'customer_type', label: 'Type' },
      { field: 'customer_group', label: 'Group' },
      { field: 'territory', label: 'Territory' },
      { field: 'mobile_no', label: 'Phone' },
    ],
    detail: {
      title: 'customer_name',
      groups: [
        {
          title: 'Customer',
          fields: [
            { field: 'customer_name', label: 'Name' },
            { field: 'customer_type', label: 'Type' },
            { field: 'customer_group', label: 'Group' },
            { field: 'territory', label: 'Territory' },
            { field: 'mobile_no', label: 'Phone' },
            { field: 'email_id', label: 'Email' },
            { field: 'tax_id', label: 'Tax ID' },
            { field: 'disabled', label: 'Disabled', type: 'check' },
          ],
        },
      ],
      related: [
        { list: 'kyc', field: 'customer', title: 'KYC' },
        { list: 'reservations', field: 'customer', title: 'Reservations' },
        { list: 'sale_quotations', field: 'customer', title: 'Sale quotations' },
        {
          list: 'contracts',
          field: 'customer',
          title: 'Contracts',
          orderBy: 'modified desc',
          columns: [
            { field: 'name', label: 'Contract', type: 'id' },
            { field: 'external_reference', label: 'Reference' },
            { field: 'signed_on', label: 'Signed', type: 'date' },
            DOC,
          ],
        },
        { list: 'title_transfers', field: 'customer', title: 'Title transfers' },
        {
          list: 'jobs',
          field: 'customer',
          title: 'Construction jobs',
          orderBy: 'modified desc',
          columns: [
            { field: 'name', label: 'Job', type: 'id' },
            { field: 'service_type', label: 'Service' },
            { field: 'site_location', label: 'Site' },
            { field: 'status', label: 'Status', type: 'status' },
          ],
        },
      ],
    },
  },
  kyc: {
    form: true,
    section: 'customers',
    title: 'KYC',
    noun: 'KYC records',
    doctype: 'Sidra Customer KYC',
    path: '/customers/kyc',
    icon: 'lucide-id-card',
    orderBy: 'modified desc',
    search: ['customer', 'customer_name', 'phone'],
    searchLabel: 'Customer or phone',
    status: { Draft: 'current', Verified: 'completed' },
    list: [
      { field: 'customer_name', label: 'Customer', type: 'id' },
      { field: 'status', label: 'Status', type: 'status' },
      { field: 'id_type', label: 'ID type' },
      { field: 'phone', label: 'Phone' },
      { field: 'verified_on', label: 'Verified', type: 'date' },
    ],
    detail: {
      title: 'customer_name',
      status: 'status',
      groups: [
        {
          title: 'Buyer',
          fields: [
            { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
            { field: 'phone', label: 'Phone' },
            { field: 'address', label: 'Address', type: 'longtext' },
            { field: 'verified_by', label: 'Verified by', type: 'user' },
            { field: 'verified_on', label: 'Verified on', type: 'datetime' },
          ],
        },
        {
          title: 'Identity document',
          fields: [
            { field: 'id_type', label: 'ID type' },
            { field: 'id_number', label: 'ID number' },
            { field: 'name_on_id', label: 'Name on ID' },
            { field: 'id_expiry', label: 'Expires', type: 'date' },
            { field: 'id_document', label: 'Document', type: 'file' },
          ],
        },
        {
          title: 'Guarantor',
          fields: [
            { field: 'guarantor_name', label: 'Name' },
            { field: 'guarantor_phone', label: 'Phone' },
            { field: 'guarantor_relationship', label: 'Relationship' },
            { field: 'guarantor_id_number', label: 'ID number' },
            { field: 'guarantor_document', label: 'Document', type: 'file' },
          ],
        },
      ],
    },
  },

  reservations: {
    form: true,
    section: 'sales',
    title: 'Reservations',
    noun: 'reservations',
    doctype: 'Sidra Reservation',
    path: '/sales/reservations',
    icon: 'lucide-bookmark',
    company: true,
    orderBy: 'creation desc',
    search: ['name', 'unit', 'customer'],
    searchLabel: 'Reservation, unit or customer',
    status: { Active: 'current', Converted: 'completed', Expired: 'muted', Cancelled: 'blocked' },
    list: [
      { field: 'name', label: 'Reservation', type: 'id' },
      { field: 'unit', label: 'Unit' },
      { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
      { field: 'reserved_on', label: 'Reserved', type: 'date' },
      { field: 'expires_on', label: 'Expires', type: 'date' },
      { field: 'status', label: 'Status', type: 'status' },
    ],
    detail: {
      subtitle: 'customer',
      status: 'status',
      groups: [
        {
          title: 'Reservation',
          fields: [
            { field: 'unit', label: 'Unit' },
            { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
            { field: 'company', label: 'Company' },
            { field: 'reserved_on', label: 'Reserved on', type: 'date' },
            { field: 'expires_on', label: 'Expires on', type: 'date' },
            { field: 'sale_contract', label: 'Sale contract', type: 'link', to: 'contracts' },
            { field: 'notes', label: 'Notes', type: 'longtext' },
          ],
        },
      ],
    },
  },
  sale_quotations: {
    form: true,
    section: 'sales',
    title: 'Quotations',
    noun: 'sale quotations',
    doctype: 'Sidra Sale Quotation',
    path: '/sales/quotations',
    icon: 'lucide-file-signature',
    company: true,
    orderBy: 'quotation_date desc, creation desc',
    search: ['name', 'customer'],
    searchLabel: 'Quotation or customer',
    status: { Draft: 'muted', Issued: 'current', Expired: 'muted', Cancelled: 'blocked' },
    list: [
      { field: 'name', label: 'Quotation', type: 'id' },
      { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
      { field: 'quotation_date', label: 'Date', type: 'date' },
      { field: 'valid_until', label: 'Valid until', type: 'date' },
      { field: 'cash_total', label: 'Cash total', type: 'money' },
      { field: 'installment_total', label: 'Installment total', type: 'money' },
      { field: 'status', label: 'Status', type: 'status' },
    ],
    extra: ['currency', 'company'],
    detail: {
      subtitle: 'customer',
      status: 'status',
      groups: [
        {
          title: 'Quotation',
          fields: [
            { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
            { field: 'company', label: 'Company' },
            { field: 'quotation_date', label: 'Date', type: 'date' },
            { field: 'valid_until', label: 'Valid until', type: 'date' },
            { field: 'contract_profile', label: 'Contract profile' },
          ],
        },
        {
          title: 'Prices',
          fields: [
            { field: 'listed_total', label: 'Listed total', type: 'money' },
            { field: 'discount_amount', label: 'Discount', type: 'money' },
            { field: 'cash_total', label: 'Cash total', type: 'money' },
            { field: 'discount_approval', label: 'Discount approval' },
            { field: 'discount_approved_by', label: 'Approved by', type: 'user' },
            { field: 'discount_approved_on', label: 'Approved on', type: 'datetime' },
          ],
        },
        {
          title: 'Installment option',
          fields: [
            { field: 'installment_total', label: 'Installment total', type: 'money' },
            { field: 'down_payment', label: 'Down payment', type: 'money' },
            { field: 'balance', label: 'Balance', type: 'money' },
            { field: 'installments', label: 'Installments', type: 'int' },
            { field: 'due_day', label: 'Due day', type: 'int' },
            { field: 'grace_months', label: 'Grace months', type: 'int' },
            { field: 'notes', label: 'Notes', type: 'longtext' },
          ],
        },
      ],
      tables: [
        {
          field: 'units',
          title: 'Units',
          columns: [
            { field: 'unit', label: 'Unit' },
            { field: 'scheme', label: 'Scheme' },
            { field: 'listed_price', label: 'Listed', type: 'money' },
            { field: 'cash_price', label: 'Cash', type: 'money' },
            { field: 'installment_price', label: 'Installment', type: 'money' },
          ],
        },
        {
          field: 'schedule',
          title: 'Installment schedule',
          columns: [
            { field: 'seq', label: 'No.', type: 'int' },
            { field: 'row_type', label: 'Type' },
            { field: 'due_date', label: 'Due date', type: 'date' },
            { field: 'amount', label: 'Amount', type: 'money' },
          ],
        },
      ],
    },
  },

  contracts: {
    section: 'contracts',
    title: 'Contracts',
    noun: 'contracts',
    doctype: 'Sidra Sale Contract',
    path: '/contracts',
    page: 'contracts',
    detailRoute: 'contract-detail',
    icon: 'lucide-file-text',
    form: true,
    // /contracts/new and /contracts/<name>/edit belong to the registration screen.
    formPaths: { new: '/contracts/new-contract', edit: '/contracts/:name/edit-contract' },
  },
  title_transfers: {
    form: true,
    section: 'contracts',
    title: 'Title transfers',
    noun: 'title transfers',
    doctype: 'Sidra Title Transfer',
    path: '/contracts/title-transfers',
    icon: 'lucide-landmark',
    company: true,
    orderBy: 'deadline_date asc, creation desc',
    search: ['name', 'contract', 'unit', 'customer'],
    searchLabel: 'Transfer, contract, unit or customer',
    status: {
      'Awaiting Final Payment': 'pending',
      'No Deadline on Contract': 'muted',
      'In Progress': 'current',
      'Due Soon': 'current',
      Overdue: 'blocked',
      'Handed Over': 'completed',
      'Handed Over Late': 'completed',
    },
    list: [
      { field: 'name', label: 'Transfer', type: 'id' },
      { field: 'contract', label: 'Contract', type: 'link', to: 'contracts' },
      { field: 'unit', label: 'Unit' },
      { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
      { field: 'deadline_date', label: 'Deadline', type: 'date' },
      { field: 'status', label: 'Status', type: 'status' },
    ],
    detail: {
      subtitle: 'customer',
      status: 'status',
      groups: [
        {
          title: 'Title',
          fields: [
            { field: 'contract', label: 'Contract', type: 'link', to: 'contracts' },
            { field: 'unit', label: 'Unit' },
            { field: 'customer', label: 'Customer', type: 'link', to: 'customers' },
            { field: 'title_deadline_days', label: 'Deadline (days)', type: 'int' },
            { field: 'deadline_date', label: 'Deadline', type: 'date' },
            { field: 'days_overdue', label: 'Days overdue', type: 'int' },
            { field: 'title_term', label: 'Contract term', type: 'longtext' },
          ],
        },
        {
          title: 'Final payment',
          fields: [
            { field: 'final_payment_date', label: 'Paid on', type: 'date' },
            { field: 'final_payment_evidence', label: 'Evidence', type: 'file' },
            { field: 'final_payment_entered_by', label: 'Entered by', type: 'user' },
            { field: 'final_payment_confirmed_by', label: 'Confirmed by', type: 'user' },
            { field: 'final_payment_confirmed_on', label: 'Confirmed on', type: 'datetime' },
          ],
        },
        {
          title: 'Land office and handover',
          fields: [
            { field: 'submitted_on', label: 'Submitted on', type: 'date' },
            { field: 'land_office_reference', label: 'Land office reference' },
            { field: 'deed_number', label: 'Deed number' },
            { field: 'deed_issued_on', label: 'Deed issued', type: 'date' },
            { field: 'handed_over_on', label: 'Handed over', type: 'date' },
            { field: 'handed_over_to', label: 'Handed over to' },
            { field: 'handover_evidence', label: 'Evidence', type: 'file' },
            { field: 'handover_confirmed_by', label: 'Confirmed by', type: 'user' },
            { field: 'handover_confirmed_on', label: 'Confirmed on', type: 'datetime' },
          ],
        },
      ],
      tables: [
        {
          field: 'documents',
          title: 'Documents',
          columns: [
            { field: 'document', label: 'Document' },
            { field: 'received', label: 'Received', type: 'check' },
            { field: 'received_on', label: 'Received on', type: 'date' },
            { field: 'file', label: 'File', type: 'file' },
          ],
        },
      ],
    },
  },

  jobs: {
    form: true,
    section: 'construction',
    title: 'Jobs',
    noun: 'construction jobs',
    doctype: 'Sidra Construction Job',
    path: '/construction',
    page: 'construction',
    detailRoute: 'construction-detail',
    icon: 'lucide-hard-hat',
    status: {
      Enquiry: 'muted',
      Quoted: 'muted',
      Contracted: 'current',
      'In Progress': 'current',
      'On Hold': 'pending',
      Completed: 'completed',
      'Defects Period': 'completed',
      Closed: 'completed',
      Cancelled: 'blocked',
    },
  },
  construction_quotations: {
    form: true,
    section: 'construction',
    title: 'Quotations',
    noun: 'construction quotations',
    doctype: 'Sidra Construction Quotation',
    path: '/construction/quotations',
    icon: 'lucide-file-signature',
    company: true,
    orderBy: 'creation desc',
    search: ['name', 'job', 'customer'],
    searchLabel: 'Quotation, job or client',
    status: { Draft: 'muted', Issued: 'current', Contracted: 'completed', Cancelled: 'blocked' },
    list: [
      { field: 'name', label: 'Quotation', type: 'id' },
      { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
      { field: 'customer', label: 'Client', type: 'link', to: 'customers' },
      { field: 'pricing_basis', label: 'Basis' },
      { field: 'quoted_amount', label: 'Quoted', type: 'money' },
      { field: 'valid_until', label: 'Valid until', type: 'date' },
      { field: 'status', label: 'Status', type: 'status' },
    ],
    extra: ['currency', 'company'],
    detail: {
      subtitle: 'customer',
      status: 'status',
      groups: [
        {
          title: 'Quotation',
          fields: [
            { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
            { field: 'customer', label: 'Client', type: 'link', to: 'customers' },
            { field: 'pricing_basis', label: 'Pricing basis' },
            { field: 'fixed_fee', label: 'Fixed fee', type: 'money' },
            { field: 'boq_total', label: 'BOQ total', type: 'money' },
            { field: 'quoted_amount', label: 'Quoted amount', type: 'money' },
            { field: 'valid_until', label: 'Valid until', type: 'date' },
            { field: 'boq_revision', label: 'BOQ revision', type: 'link', to: 'boq_revisions' },
          ],
        },
        {
          title: 'Terms',
          fields: [
            { field: 'start_date', label: 'Start', type: 'date' },
            { field: 'duration_days', label: 'Duration (days)', type: 'int' },
            { field: 'end_date', label: 'End', type: 'date' },
            { field: 'retention_pct', label: 'Retention', type: 'percent' },
            { field: 'retention_period_months', label: 'Retention period (months)', type: 'int' },
            { field: 'scope', label: 'Scope', type: 'longtext' },
          ],
        },
        {
          title: 'Acceptance',
          fields: [
            { field: 'client_accepted_by', label: 'Accepted by (client)' },
            { field: 'client_accepted_on', label: 'Accepted on', type: 'date' },
            { field: 'client_acceptance_document', label: 'Acceptance document', type: 'file' },
            { field: 'contract_approved_by', label: 'Contract approved by', type: 'user' },
            { field: 'contract_approved_on', label: 'Approved on', type: 'datetime' },
          ],
        },
      ],
      tables: [{ field: 'boq', title: 'Bill of quantities', columns: 'boq' }],
    },
  },
  boq_revisions: {
    form: true,
    section: 'construction',
    title: 'BOQ revisions',
    noun: 'BOQ revisions',
    doctype: 'Sidra BOQ Revision',
    path: '/construction/boq-revisions',
    icon: 'lucide-list-ordered',
    company: true,
    orderBy: 'creation desc',
    search: ['name', 'job', 'customer'],
    searchLabel: 'Revision, job or client',
    list: [
      { field: 'name', label: 'Revision', type: 'id' },
      { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
      { field: 'revision_no', label: 'No.', type: 'int' },
      { field: 'previous_total', label: 'Previous total', type: 'money' },
      { field: 'boq_total', label: 'New total', type: 'money' },
      { field: 'difference', label: 'Difference', type: 'money' },
      DOC,
    ],
    extra: ['currency', 'company'],
    detail: {
      subtitle: 'job',
      groups: [
        {
          title: 'Revision',
          fields: [
            { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
            { field: 'customer', label: 'Client', type: 'link', to: 'customers' },
            { field: 'revision_no', label: 'Revision', type: 'int' },
            { field: 'base_revision', label: 'Based on', type: 'link', to: 'boq_revisions' },
            { field: 'previous_total', label: 'Previous total', type: 'money' },
            { field: 'boq_total', label: 'New total', type: 'money' },
            { field: 'difference', label: 'Difference', type: 'money' },
            { field: 'approved_by', label: 'Approved by', type: 'user' },
            { field: 'approved_on', label: 'Approved on', type: 'datetime' },
            { field: 'reason', label: 'Reason', type: 'longtext' },
          ],
        },
      ],
      tables: [{ field: 'boq', title: 'Bill of quantities', columns: 'boq' }],
    },
  },
  variations: {
    form: true,
    section: 'construction',
    title: 'Variations',
    noun: 'variation orders',
    doctype: 'Sidra Variation Order',
    path: '/construction/variations',
    icon: 'lucide-git-compare',
    company: true,
    orderBy: 'creation desc',
    search: ['name', 'job', 'customer'],
    searchLabel: 'Variation, job or client',
    list: [
      { field: 'name', label: 'Variation', type: 'id' },
      { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
      { field: 'customer', label: 'Client', type: 'link', to: 'customers' },
      { field: 'amount', label: 'Amount', type: 'money' },
      { field: 'approved_on', label: 'Approved', type: 'date' },
      DOC,
    ],
    extra: ['currency', 'company'],
    detail: {
      subtitle: 'job',
      groups: [
        {
          title: 'Variation',
          fields: [
            { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
            { field: 'customer', label: 'Client', type: 'link', to: 'customers' },
            { field: 'amount', label: 'Amount', type: 'money' },
            { field: 'contract_value_before', label: 'Contract value before', type: 'money' },
            { field: 'contract_value_after', label: 'Contract value after', type: 'money' },
            { field: 'boq_revision', label: 'BOQ revision', type: 'link', to: 'boq_revisions' },
            { field: 'description', label: 'Description', type: 'longtext' },
          ],
        },
        {
          title: 'Approval',
          fields: [
            { field: 'client_approved_by', label: 'Client approved by' },
            { field: 'client_approved_on', label: 'Client approved on', type: 'date' },
            { field: 'client_approval_document', label: 'Client approval', type: 'file' },
            { field: 'approved_by', label: 'Approved by', type: 'user' },
            { field: 'approved_on', label: 'Approved on', type: 'datetime' },
          ],
        },
      ],
    },
  },
  inspections: {
    form: true,
    section: 'construction',
    title: 'Inspections',
    noun: 'inspection reports',
    doctype: 'Sidra Inspection Report',
    path: '/construction/inspections',
    icon: 'lucide-clipboard-check',
    company: true,
    orderBy: 'inspection_date desc, creation desc',
    search: ['name', 'job', 'customer', 'stage'],
    searchLabel: 'Report, job, client or stage',
    status: { Pass: 'completed', 'Pass with defects': 'current', Fail: 'blocked' },
    list: [
      { field: 'name', label: 'Report', type: 'id' },
      { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
      { field: 'stage', label: 'Stage' },
      { field: 'inspection_date', label: 'Date', type: 'date' },
      { field: 'inspector', label: 'Inspector', type: 'user' },
      { field: 'result', label: 'Result', type: 'status' },
      DOC,
    ],
    detail: {
      subtitle: 'job',
      status: 'result',
      groups: [
        {
          title: 'Inspection',
          fields: [
            { field: 'job', label: 'Job', type: 'link', to: 'jobs' },
            { field: 'customer', label: 'Client', type: 'link', to: 'customers' },
            { field: 'stage', label: 'Stage' },
            { field: 'inspection_date', label: 'Date', type: 'date' },
            { field: 'inspector', label: 'Inspector', type: 'user' },
            { field: 'result', label: 'Result' },
          ],
        },
        {
          title: 'Findings',
          fields: [
            { field: 'defects_found', label: 'Defects found', type: 'longtext' },
            { field: 'next_action', label: 'Next action', type: 'longtext' },
            { field: 'next_action_due', label: 'Next action due', type: 'date' },
          ],
        },
      ],
      tables: [
        {
          field: 'checklist',
          title: 'Checklist',
          columns: [
            { field: 'item', label: 'Item' },
            { field: 'result', label: 'Result' },
            { field: 'remarks', label: 'Remarks' },
          ],
        },
        {
          field: 'photos',
          title: 'Photos',
          columns: [
            { field: 'caption', label: 'Caption' },
            { field: 'photo', label: 'Photo', type: 'file' },
          ],
        },
      ],
    },
  },
}

const BOQ_COLUMNS = [
  { field: 'cost_code', label: 'Code' },
  { field: 'description', label: 'Description' },
  { field: 'uom', label: 'Unit' },
  { field: 'qty', label: 'Qty', type: 'number' },
  { field: 'rate', label: 'Rate', type: 'money' },
  { field: 'amount', label: 'Amount', type: 'money' },
]
for (const config of Object.values(RECORDS)) {
  for (const table of config.detail?.tables ?? []) if (table.columns === 'boq') table.columns = BOQ_COLUMNS
}

// Sections in navigation order, with their lists. A section shows only the lists the server allows.
export const SECTIONS = {
  properties: ['units', 'schemes', 'price_history'],
  customers: ['customers', 'kyc'],
  sales: ['reservations', 'sale_quotations'],
  contracts: ['contracts', 'title_transfers'],
  construction: ['jobs', 'construction_quotations', 'boq_revisions', 'variations', 'inspections'],
}

/** Lists that use the generic list and detail screens (the others have pages of their own). */
export const GENERIC = Object.keys(RECORDS).filter((key) => !RECORDS[key].page)

export const listRoute = (key) => (RECORDS[key].page ? RECORDS[key].page : `${key}-list`)
export const detailRoute = (key) => RECORDS[key].detailRoute || `${key}-detail`

/** The router location of a record, or null when the interface has no screen for that list. */
export function recordRoute(key, name) {
  if (!RECORDS[key] || !name) return null
  if (RECORDS[key].page && !RECORDS[key].detailRoute && !RECORDS[key].detail) return null
  return { name: detailRoute(key), params: { name } }
}
