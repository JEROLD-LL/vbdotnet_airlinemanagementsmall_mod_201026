Imports System.Windows.Forms

Public Class ProfileForm
    Inherits Form

    Private user As User
    Private lblUsername As Label
    Private lblEmail As Label
    Private lblFullName As Label
    Private lblCreatedAt As Label
    Private btnEdit As Button
    Private btnClose As Button

    Public Sub New()
        InitializeComponent()
        LoadProfile()
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "My Profile"
        Me.Size = New Size(500, 300)
        Me.StartPosition = FormStartPosition.CenterScreen
        Me.FormBorderStyle = FormBorderStyle.FixedDialog
        Me.MaximizeBox = False

        Dim yPos As Integer = 20

        ' Username
        lblUsername = New Label()
        lblUsername.Text = "Username:"
        lblUsername.AutoSize = True
        lblUsername.Location = New Point(20, yPos)
        Me.Controls.Add(lblUsername)

        Dim lblUsernameValue As New Label()
        lblUsernameValue.AutoSize = True
        lblUsernameValue.Location = New Point(150, yPos)
        lblUsernameValue.Font = New Font("Arial", 10, FontStyle.Bold)
        Me.Controls.Add(lblUsernameValue)
        yPos += 30

        ' Email
        lblEmail = New Label()
        lblEmail.Text = "Email:"
        lblEmail.AutoSize = True
        lblEmail.Location = New Point(20, yPos)
        Me.Controls.Add(lblEmail)

        Dim lblEmailValue As New Label()
        lblEmailValue.AutoSize = True
        lblEmailValue.Location = New Point(150, yPos)
        Me.Controls.Add(lblEmailValue)
        yPos += 30

        ' Full Name
        lblFullName = New Label()
        lblFullName.Text = "Full Name:"
        lblFullName.AutoSize = True
        lblFullName.Location = New Point(20, yPos)
        Me.Controls.Add(lblFullName)

        Dim lblFullNameValue As New Label()
        lblFullNameValue.AutoSize = True
        lblFullNameValue.Location = New Point(150, yPos)
        Me.Controls.Add(lblFullNameValue)
        yPos += 30

        ' Member Since
        lblCreatedAt = New Label()
        lblCreatedAt.Text = "Member Since:"
        lblCreatedAt.AutoSize = True
        lblCreatedAt.Location = New Point(20, yPos)
        Me.Controls.Add(lblCreatedAt)

        Dim lblCreatedAtValue As New Label()
        lblCreatedAtValue.AutoSize = True
        lblCreatedAtValue.Location = New Point(150, yPos)
        Me.Controls.Add(lblCreatedAtValue)
        yPos += 50

        ' Buttons
        btnEdit = New Button()
        btnEdit.Text = "Edit Profile"
        btnEdit.Location = New Point(20, yPos)
        btnEdit.Size = New Size(150, 30)
        AddHandler btnEdit.Click, AddressOf BtnEdit_Click
        Me.Controls.Add(btnEdit)

        btnClose = New Button()
        btnClose.Text = "Close"
        btnClose.Location = New Point(320, yPos)
        btnClose.Size = New Size(150, 30)
        AddHandler btnClose.Click, AddressOf BtnClose_Click
        Me.Controls.Add(btnClose)

        ' Store references for updating
        Me.Tag = New Object() {lblUsernameValue, lblEmailValue, lblFullNameValue, lblCreatedAtValue}
    End Sub

    Private Sub LoadProfile()
        If Not SessionManager.IsAuthenticated() Then
            MessageBox.Show("Please login first.", "Not Authenticated", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Me.Close()
            Return
        End If

        user = UserRepository.GetById(SessionManager.CurrentUser.Id)
        If user Is Nothing Then
            MessageBox.Show("User not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Me.Close()
            Return
        End If

        Dim labels As Object() = CType(Me.Tag, Object())
        CType(labels(0), Label).Text = user.Username & " (cannot be changed)"
        CType(labels(1), Label).Text = user.Email
        CType(labels(2), Label).Text = user.FullName
        CType(labels(3), Label).Text = user.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss")
    End Sub

    Private Sub BtnEdit_Click(sender As Object, e As EventArgs)
        Dim editForm As New EditProfileForm()
        editForm.ShowDialog()
        LoadProfile()
    End Sub

    Private Sub BtnClose_Click(sender As Object, e As EventArgs)
        Me.Close()
    End Sub
End Class

