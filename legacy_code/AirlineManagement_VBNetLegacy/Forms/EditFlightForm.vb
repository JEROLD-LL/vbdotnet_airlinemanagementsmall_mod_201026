Imports System.Windows.Forms

Public Class EditFlightForm
    Inherits Form

    Private flight As Flight
    Private lblFlightNumber As Label
    Private lblOrigin As Label
    Private lblDestination As Label
    Private lblDepartureDate As Label
    Private lblDepartureTime As Label
    Private lblArrivalTime As Label
    Private lblPrice As Label
    Private lblAvailableSeats As Label
    Private txtFlightNumber As TextBox
    Private txtOrigin As TextBox
    Private txtDestination As TextBox
    Private dtpDepartureDate As DateTimePicker
    Private dtpDepartureTime As DateTimePicker
    Private dtpArrivalTime As DateTimePicker
    Private txtPrice As TextBox
    Private txtAvailableSeats As TextBox
    Private btnUpdate As Button
    Private btnCancel As Button
    Private lblError As Label

    Public Sub New(selectedFlightId As Integer)
        InitializeComponent()
        LoadFlight(selectedFlightId)
    End Sub

    Private Sub InitializeComponent()
        Me.Text = "Edit Flight"
        Me.Size = New Size(500, 500)
        Me.StartPosition = FormStartPosition.CenterScreen
        Me.FormBorderStyle = FormBorderStyle.FixedDialog
        Me.MaximizeBox = False

        Dim yPos As Integer = 20

        ' Flight Number
        lblFlightNumber = New Label()
        lblFlightNumber.Text = "Flight Number: *"
        lblFlightNumber.AutoSize = True
        lblFlightNumber.Location = New Point(20, yPos)
        Me.Controls.Add(lblFlightNumber)

        txtFlightNumber = New TextBox()
        txtFlightNumber.Location = New Point(20, yPos + 20)
        txtFlightNumber.Size = New Size(450, 25)
        Me.Controls.Add(txtFlightNumber)
        yPos += 50

        ' Origin
        lblOrigin = New Label()
        lblOrigin.Text = "Origin: *"
        lblOrigin.AutoSize = True
        lblOrigin.Location = New Point(20, yPos)
        Me.Controls.Add(lblOrigin)

        txtOrigin = New TextBox()
        txtOrigin.Location = New Point(20, yPos + 20)
        txtOrigin.Size = New Size(450, 25)
        Me.Controls.Add(txtOrigin)
        yPos += 50

        ' Destination
        lblDestination = New Label()
        lblDestination.Text = "Destination: *"
        lblDestination.AutoSize = True
        lblDestination.Location = New Point(20, yPos)
        Me.Controls.Add(lblDestination)

        txtDestination = New TextBox()
        txtDestination.Location = New Point(20, yPos + 20)
        txtDestination.Size = New Size(450, 25)
        Me.Controls.Add(txtDestination)
        yPos += 50

        ' Departure Date
        lblDepartureDate = New Label()
        lblDepartureDate.Text = "Departure Date: *"
        lblDepartureDate.AutoSize = True
        lblDepartureDate.Location = New Point(20, yPos)
        Me.Controls.Add(lblDepartureDate)

        dtpDepartureDate = New DateTimePicker()
        dtpDepartureDate.Location = New Point(20, yPos + 20)
        dtpDepartureDate.Size = New Size(450, 25)
        dtpDepartureDate.Format = DateTimePickerFormat.Short
        Me.Controls.Add(dtpDepartureDate)
        yPos += 50

        ' Departure Time
        lblDepartureTime = New Label()
        lblDepartureTime.Text = "Departure Time: *"
        lblDepartureTime.AutoSize = True
        lblDepartureTime.Location = New Point(20, yPos)
        Me.Controls.Add(lblDepartureTime)

        dtpDepartureTime = New DateTimePicker()
        dtpDepartureTime.Location = New Point(20, yPos + 20)
        dtpDepartureTime.Size = New Size(450, 25)
        dtpDepartureTime.Format = DateTimePickerFormat.Time
        dtpDepartureTime.ShowUpDown = True
        Me.Controls.Add(dtpDepartureTime)
        yPos += 50

        ' Arrival Time
        lblArrivalTime = New Label()
        lblArrivalTime.Text = "Arrival Time: *"
        lblArrivalTime.AutoSize = True
        lblArrivalTime.Location = New Point(20, yPos)
        Me.Controls.Add(lblArrivalTime)

        dtpArrivalTime = New DateTimePicker()
        dtpArrivalTime.Location = New Point(20, yPos + 20)
        dtpArrivalTime.Size = New Size(450, 25)
        dtpArrivalTime.Format = DateTimePickerFormat.Time
        dtpArrivalTime.ShowUpDown = True
        Me.Controls.Add(dtpArrivalTime)
        yPos += 50

        ' Price
        lblPrice = New Label()
        lblPrice.Text = "Price: *"
        lblPrice.AutoSize = True
        lblPrice.Location = New Point(20, yPos)
        Me.Controls.Add(lblPrice)

        txtPrice = New TextBox()
        txtPrice.Location = New Point(20, yPos + 20)
        txtPrice.Size = New Size(450, 25)
        Me.Controls.Add(txtPrice)
        yPos += 50

        ' Available Seats
        lblAvailableSeats = New Label()
        lblAvailableSeats.Text = "Available Seats: *"
        lblAvailableSeats.AutoSize = True
        lblAvailableSeats.Location = New Point(20, yPos)
        Me.Controls.Add(lblAvailableSeats)

        txtAvailableSeats = New TextBox()
        txtAvailableSeats.Location = New Point(20, yPos + 20)
        txtAvailableSeats.Size = New Size(450, 25)
        Me.Controls.Add(txtAvailableSeats)
        yPos += 50

        ' Error label
        lblError = New Label()
        lblError.ForeColor = Color.Red
        lblError.AutoSize = True
        lblError.Location = New Point(20, yPos)
        lblError.Size = New Size(450, 40)
        Me.Controls.Add(lblError)
        yPos += 50

        ' Buttons
        btnUpdate = New Button()
        btnUpdate.Text = "Update Flight"
        btnUpdate.Location = New Point(20, yPos)
        btnUpdate.Size = New Size(150, 30)
        AddHandler btnUpdate.Click, AddressOf BtnUpdate_Click
        Me.Controls.Add(btnUpdate)

        btnCancel = New Button()
        btnCancel.Text = "Cancel"
        btnCancel.Location = New Point(320, yPos)
        btnCancel.Size = New Size(150, 30)
        AddHandler btnCancel.Click, AddressOf BtnCancel_Click
        Me.Controls.Add(btnCancel)

        Me.AcceptButton = btnUpdate
    End Sub

    Private Sub LoadFlight(flightId As Integer)
        flight = FlightRepository.GetById(flightId)
        If flight Is Nothing Then
            MessageBox.Show("Flight not found.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Me.Close()
            Return
        End If

        txtFlightNumber.Text = flight.FlightNumber
        txtOrigin.Text = flight.Origin
        txtDestination.Text = flight.Destination
        dtpDepartureDate.Value = flight.DepartureDate
        dtpDepartureTime.Value = DateTime.Today.Add(flight.DepartureTime)
        dtpArrivalTime.Value = DateTime.Today.Add(flight.ArrivalTime)
        txtPrice.Text = flight.Price.ToString()
        txtAvailableSeats.Text = flight.AvailableSeats.ToString()
    End Sub

    Private Sub BtnUpdate_Click(sender As Object, e As EventArgs)
        lblError.Text = ""

        Dim errors As New List(Of String)

        Dim flightNumber As String = txtFlightNumber.Text.Trim()
        Dim origin As String = txtOrigin.Text.Trim()
        Dim destination As String = txtDestination.Text.Trim()
        Dim departureDate As DateTime = dtpDepartureDate.Value.Date
        Dim departureTime As TimeSpan = dtpDepartureTime.Value.TimeOfDay
        Dim arrivalTime As TimeSpan = dtpArrivalTime.Value.TimeOfDay
        Dim price As Decimal
        Dim availableSeats As Integer

        If String.IsNullOrWhiteSpace(flightNumber) Then
            errors.Add("Flight number is required.")
        ElseIf flightNumber <> flight.FlightNumber AndAlso FlightRepository.FlightNumberExists(flightNumber) Then
            errors.Add("Flight number already exists. Please use a unique flight number.")
        End If

        If String.IsNullOrWhiteSpace(origin) Then
            errors.Add("Origin is required.")
        End If

        If String.IsNullOrWhiteSpace(destination) Then
            errors.Add("Destination is required.")
        End If

        If Not Decimal.TryParse(txtPrice.Text, price) Then
            errors.Add("Valid price is required.")
        Else
            errors.AddRange(ValidationHelper.ValidatePrice(price))
        End If

        If Not Integer.TryParse(txtAvailableSeats.Text, availableSeats) Then
            errors.Add("Valid available seats is required.")
        Else
            errors.AddRange(ValidationHelper.ValidateAvailableSeats(availableSeats))
        End If

        If errors.Count > 0 Then
            lblError.Text = String.Join(vbCrLf, errors)
            Return
        End If

        flight.FlightNumber = flightNumber
        flight.Origin = origin
        flight.Destination = destination
        flight.DepartureDate = departureDate
        flight.DepartureTime = departureTime
        flight.ArrivalTime = arrivalTime
        flight.Price = price
        flight.AvailableSeats = availableSeats

        Try
            FlightRepository.Update(flight)
            MessageBox.Show("Flight updated successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
            Me.Close()
        Catch ex As Exception
            lblError.Text = "An error occurred: " & ex.Message
        End Try
    End Sub

    Private Sub BtnCancel_Click(sender As Object, e As EventArgs)
        Me.Close()
    End Sub
End Class

