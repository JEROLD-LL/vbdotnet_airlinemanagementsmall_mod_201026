Imports System.Windows.Forms

Public Class BookFlightForm
    Inherits Form

    Private flightId As Integer
    Private flight As Flight
    Private lblFlightInfo As Label
    Private lblPassengerName As Label
    Private lblPassengerEmail As Label
    Private lblSeatNumber As Label
    Private txtPassengerName As TextBox
    Private txtPassengerEmail As TextBox
    Private txtSeatNumber As TextBox
    Private btnBook As Button
    Private btnCancel As Button
    Private lblError As Label

    Public Sub New(selectedFlightId As Integer)
        flightId = selectedFlightId
        InitializeComponent()
        LoadFlight()
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "Book Flight"
        Me.Size = New Size(500, 400)
        Me.StartPosition = FormStartPosition.CenterScreen
        Me.FormBorderStyle = FormBorderStyle.FixedDialog
        Me.MaximizeBox = False

        ' Flight Info
        lblFlightInfo = New Label()
        lblFlightInfo.Location = New Point(20, 20)
        lblFlightInfo.Size = New Size(450, 100)
        lblFlightInfo.AutoSize = False
        Me.Controls.Add(lblFlightInfo)

        ' Passenger Name
        lblPassengerName = New Label()
        lblPassengerName.Text = "Passenger Name: *"
        lblPassengerName.AutoSize = True
        lblPassengerName.Location = New Point(20, 130)
        Me.Controls.Add(lblPassengerName)

        txtPassengerName = New TextBox()
        txtPassengerName.Location = New Point(20, 150)
        txtPassengerName.Size = New Size(450, 25)
        Me.Controls.Add(txtPassengerName)

        ' Passenger Email
        lblPassengerEmail = New Label()
        lblPassengerEmail.Text = "Passenger Email: *"
        lblPassengerEmail.AutoSize = True
        lblPassengerEmail.Location = New Point(20, 180)
        Me.Controls.Add(lblPassengerEmail)

        txtPassengerEmail = New TextBox()
        txtPassengerEmail.Location = New Point(20, 200)
        txtPassengerEmail.Size = New Size(450, 25)
        Me.Controls.Add(txtPassengerEmail)

        ' Seat Number
        lblSeatNumber = New Label()
        lblSeatNumber.Text = "Seat Number (Optional):"
        lblSeatNumber.AutoSize = True
        lblSeatNumber.Location = New Point(20, 230)
        Me.Controls.Add(lblSeatNumber)

        txtSeatNumber = New TextBox()
        txtSeatNumber.Location = New Point(20, 250)
        txtSeatNumber.Size = New Size(450, 25)
        Me.Controls.Add(txtSeatNumber)

        ' Error label
        lblError = New Label()
        lblError.ForeColor = Color.Red
        lblError.AutoSize = True
        lblError.Location = New Point(20, 280)
        lblError.Size = New Size(450, 40)
        Me.Controls.Add(lblError)

        ' Buttons
        btnBook = New Button()
        btnBook.Text = "Book Flight"
        btnBook.Location = New Point(20, 320)
        btnBook.Size = New Size(120, 30)
        AddHandler btnBook.Click, AddressOf BtnBook_Click
        Me.Controls.Add(btnBook)

        btnCancel = New Button()
        btnCancel.Text = "Cancel"
        btnCancel.Location = New Point(350, 320)
        btnCancel.Size = New Size(120, 30)
        AddHandler btnCancel.Click, AddressOf BtnCancel_Click
        Me.Controls.Add(btnCancel)

        Me.AcceptButton = btnBook
    End Sub

    Private Sub LoadFlight()
        flight = FlightRepository.GetById(flightId)
        If flight Is Nothing Then
            MessageBox.Show("Flight not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Me.Close()
            Return
        End If

        If flight.AvailableSeats < 1 Then
            MessageBox.Show("No available seats on this flight.", "Not Available", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Me.Close()
            Return
        End If

        lblFlightInfo.Text = "Flight: " & flight.FlightNumber & vbCrLf &
                            "Route: " & flight.Origin & " → " & flight.Destination & vbCrLf &
                            "Departure: " & flight.DepartureDate.ToString("yyyy-MM-dd") & " at " & flight.DepartureTime.ToString("hh\:mm") & vbCrLf &
                            "Price: " & flight.Price.ToString("C")
    End Sub

    Private Sub BtnBook_Click(sender As Object, e As EventArgs)
        lblError.Text = ""

        Dim passengerName As String = txtPassengerName.Text.Trim()
        Dim passengerEmail As String = txtPassengerEmail.Text.Trim()
        Dim seatNumber As String = txtSeatNumber.Text.Trim()

        Dim userId As Integer? = If(SessionManager.IsAuthenticated(), SessionManager.CurrentUser.Id, Nothing)
        Dim errorMsg As String = BookingService.CreateBooking(flightId, userId, passengerName, passengerEmail, seatNumber)

        If Not String.IsNullOrEmpty(errorMsg) Then
            lblError.Text = errorMsg
        Else
            MessageBox.Show("Booking successful!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
            Me.Close()
        End If
    End Sub

    Private Sub BtnCancel_Click(sender As Object, e As EventArgs)
        Me.Close()
    End Sub
End Class

