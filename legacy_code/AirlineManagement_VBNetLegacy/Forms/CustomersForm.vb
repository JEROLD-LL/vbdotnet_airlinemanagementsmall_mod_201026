Imports System.Windows.Forms

Public Class CustomersForm
    Inherits Form

    Private dgvCustomers As DataGridView
    Private btnRefresh As Button

    Public Sub New()
        InitializeComponent()
        LoadCustomers()
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "Customers"
        Me.Size = New Size(800, 500)
        Me.StartPosition = FormStartPosition.CenterScreen

        ' Data Grid View
        dgvCustomers = New DataGridView()
        dgvCustomers.Location = New Point(10, 10)
        dgvCustomers.Size = New Size(760, 400)
        dgvCustomers.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        dgvCustomers.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        dgvCustomers.ReadOnly = True
        dgvCustomers.AllowUserToAddRows = False
        Me.Controls.Add(dgvCustomers)

        ' Refresh button
        btnRefresh = New Button()
        btnRefresh.Text = "Refresh"
        btnRefresh.Location = New Point(10, 420)
        btnRefresh.Size = New Size(100, 30)
        AddHandler btnRefresh.Click, AddressOf BtnRefresh_Click
        Me.Controls.Add(btnRefresh)
    End Sub

    Private Sub LoadCustomers()
        Dim users As List(Of User) = UserRepository.GetAll()

        dgvCustomers.Columns.Clear()
        dgvCustomers.Columns.Add("Id", "ID")
        dgvCustomers.Columns.Add("Username", "Username")
        dgvCustomers.Columns.Add("Email", "Email")
        dgvCustomers.Columns.Add("FullName", "Full Name")
        dgvCustomers.Columns.Add("Role", "Role")
        dgvCustomers.Columns.Add("CreatedAt", "Member Since")

        dgvCustomers.Rows.Clear()
        For Each user In users
            Dim roleDisplay As String = If(user.Role = "admin", "Admin", "User")
            dgvCustomers.Rows.Add(user.Id, user.Username, user.Email, user.FullName, roleDisplay, user.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss"))
        Next
    End Sub

    Private Sub BtnRefresh_Click(sender As Object, e As EventArgs)
        LoadCustomers()
    End Sub
End Class

