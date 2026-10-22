Imports System.Windows.Forms
Imports System.Text.RegularExpressions

Public Class EditBookingForm
    Inherits Form

    Private booking As Booking
    Private lblBookingInfo As Label
    Private lblPassengerName As Label
    Private lblPassengerEmail As Label
    Private lblSeatNumber As Label
    Private txtPassengerName As TextBox
    Private txtPassengerEmail As TextBox
    Private txtSeatNumber As TextBox
    Private btnUpdate As Button
    Private btnCancel As Button
    Private lblError As Label

    Public Sub New(selectedBookingId As Integer)
        InitializeComponent()
        LoadBooking(selectedBookingId)
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "Edit Booking"
        Me.Size = New Size(500, 400)
        Me.StartPosition = FormStartPosition.CenterScreen
        Me.FormBorderStyle = FormBorderStyle.FixedDialog
        Me.MaximizeBox = False

        lblBookingInfo = New Label()
        lblBookingInfo.Location = New Point(20, 20)
        lblBookingInfo.Size = New Size(450, 60)
        lblBookingInfo.AutoSize = False
        Me.Controls.Add(lblBookingInfo)

        lblPassengerName = New Label()
        lblPassengerName.Text = "Passenger Name: *"
        lblPassengerName.AutoSize = True
        lblPassengerName.Location = New Point(20, 90)
        Me.Controls.Add(lblPassengerName)

        txtPassengerName = New TextBox()
        txtPassengerName.Location = New Point(20, 110)
        txtPassengerName.Size = New Size(450, 25)
        Me.Controls.Add(txtPassengerName)

        lblPassengerEmail = New Label()
        lblPassengerEmail.Text = "Passenger Email: *"
        lblPassengerEmail.AutoSize = True
        lblPassengerEmail.Location = New Point(20, 140)
        Me.Controls.Add(lblPassengerEmail)

        txtPassengerEmail = New TextBox()
        txtPassengerEmail.Location = New Point(20, 160)
        txtPassengerEmail.Size = New Size(450, 25)
        Me.Controls.Add(txtPassengerEmail)

        lblSeatNumber = New Label()
        lblSeatNumber.Text = "Seat Number (Optional):"
        lblSeatNumber.AutoSize = True
        lblSeatNumber.Location = New Point(20, 190)
        Me.Controls.Add(lblSeatNumber)

        txtSeatNumber = New TextBox()
        txtSeatNumber.Location = New Point(20, 210)
        txtSeatNumber.Size = New Size(450, 25)
        Me.Controls.Add(txtSeatNumber)

        lblError = New Label()
        lblError.ForeColor = Color.Red
        lblError.AutoSize = True
        lblError.Location = New Point(20, 240)
        lblError.Size = New Size(450, 40)
        Me.Controls.Add(lblError)

        btnUpdate = New Button()
        btnUpdate.Text = "Update Booking"
        btnUpdate.Location = New Point(20, 280)
        btnUpdate.Size = New Size(150, 30)
        AddHandler btnUpdate.Click, AddressOf BtnUpdate_Click
        Me.Controls.Add(btnUpdate)

        btnCancel = New Button()
        btnCancel.Text = "Cancel"
        btnCancel.Location = New Point(320, 280)
        btnCancel.Size = New Size(150, 30)
        AddHandler btnCancel.Click, AddressOf BtnCancel_Click
        Me.Controls.Add(btnCancel)

        Me.AcceptButton = btnUpdate
    End Sub

    Private Sub LoadBooking(bookingId As Integer)
        booking = BookingRepository.GetById(bookingId)
        If booking Is Nothing Then
            MessageBox.Show("Booking not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Me.Close()
            Return
        End If

        If SessionManager.IsAuthenticated() AndAlso booking.UserId.HasValue AndAlso booking.UserId.Value <> SessionManager.CurrentUser.Id Then
            MessageBox.Show("Access denied. You can only edit your own bookings.", "Access Denied", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Me.Close()
            Return
        End If

        Dim flight As Flight = FlightRepository.GetById(booking.FlightId)
        lblBookingInfo.Text = "Booking ID: #" & booking.Id & vbCrLf &
                            "Flight: " & flight.FlightNumber & " (" & flight.Origin & " → " & flight.Destination & ")"

        txtPassengerName.Text = booking.PassengerName
        txtPassengerEmail.Text = booking.PassengerEmail
        txtSeatNumber.Text = booking.SeatNumber
    End Sub

    Private Sub BtnUpdate_Click(sender As Object, e As EventArgs)
        lblError.Text = ""

        Dim errors As New List(Of String)

        Dim passengerName As String = txtPassengerName.Text.Trim()
        Dim passengerEmail As String = txtPassengerEmail.Text.Trim()
        Dim seatNumber As String = txtSeatNumber.Text.Trim()

        ' Validate passenger name
        If String.IsNullOrWhiteSpace(passengerName) Then
            errors.Add("Passenger name is required.")
        ElseIf passengerName.Length < 2 OrElse passengerName.Length > 255 Then
            errors.Add("Passenger name must be between 2 and 255 characters.")
        ElseIf Not Regex.IsMatch(passengerName, "^[a-zA-Z\s'-]+$") Then
            errors.Add("Passenger name can only contain letters, spaces, hyphens, and apostrophes.")
        End If

        ' Validate email
        If String.IsNullOrWhiteSpace(passengerEmail) Then
            errors.Add("Email is required.")
        ElseIf Not Regex.IsMatch(passengerEmail, "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$") Then
            errors.Add("Invalid email format.")
        ElseIf passengerEmail.Length > 255 Then
            errors.Add("Email must be 255 characters or less.")
        End If

        ' Validate seat number
        If Not String.IsNullOrWhiteSpace(seatNumber) Then
            If seatNumber.Length > 10 Then
                errors.Add("Seat number must be 10 characters or less.")
            ElseIf Not Regex.IsMatch(seatNumber, "^[0-9]{1,3}[A-Z]{1,2}$", RegexOptions.IgnoreCase) Then
                errors.Add("Seat number format is invalid. Use format like '12A' or '123AB'.")
            End If
        End If

        If errors.Count > 0 Then
            lblError.Text = String.Join(vbCrLf, errors)
            Return
        End If

        booking.PassengerName = passengerName
        booking.PassengerEmail = passengerEmail
        booking.SeatNumber = If(String.IsNullOrWhiteSpace(seatNumber), String.Empty, seatNumber.ToUpper())

        Try
            BookingRepository.Update(booking)
            MessageBox.Show("Booking updated successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
            Me.Close()
        Catch ex As Exception
            lblError.Text = "An error occurred: " & ex.Message
        End Try
    End Sub

    Private Sub BtnCancel_Click(sender As Object, e As EventArgs)
        Me.Close()
    End Sub
End Class

