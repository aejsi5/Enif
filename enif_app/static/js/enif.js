"use strict";

$(document).ready(function (){
    var E = new Enif();;
    $('.enif_icon_div').click(function(){
        if ($('.enif_input').hasClass('animate__backOutDown')){
            $('.enif_input').removeClass('animate__backOutDown');
            $('.enif_input').addClass('animate__backInUp')
        } else if ($('.enif_input').hasClass('animate__backInUp')) {
            $('.enif_input').removeClass('animate__backInUp');
            $('.enif_input').addClass('animate__backOutDown')
        } else {
            $('.enif_input').addClass('animate__backOutDown')
        }
        if ($('.enif_messages_container').not('.hide')){
            $('.enif_messages_container').addClass('hide');
        }
        if (!$('.enif_input').hasClass('enif_deactiv') && $('.enif_input').hasClass('animate__backOutDown')) {
            $('.enif_messages_container').addClass('hide');
        } else if (!$('.enif_input').hasClass('enif_deactiv') && $('.enif_input').hasClass('animate__backInUp')){
            $('.enif_messages_container').removeClass('hide');
        }
    });
    $('.enif_mes_input').focus(function(){
        if ($('.enif_input').hasClass('enif_deactiv')){
            $('.enif_input').removeClass('enif_deactiv');
        }
        $('.enif_messages_container').removeClass('hide');
    })
    $(".enif_mes_input").on('keyup', function (e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            var text = $(".enif_mes_input").val();
            if(text){
                E.post(text, true, null);
                $(".enif_mes_input").val(null);
            }
        }
    });
    $('.enif_send').click(function () {
        var text = $(".enif_mes_input").val();
        if (text) {
            E.post(text, true, null);
            $(".enif_mes_input").val(null);
        }
    });
    $(document).on("click", "div.enif_option", function(){
        console.log("clicked");
        var intent = $(this).data("intent_id");
        var text = $(this).find('.enif_options_text').text();
        console.log(intent);
        console.log(text);
        E.post(text, false, null, intent);
    });
    $('.enif_privacy_accept').click(function(){
        E.initiate();
        $('.enif_mes_input').focus();
        $('.enif_message_privacy').hide();
    });
});

function getCookieValue(a) {
    var b = document.cookie.match('(^|;)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

class Enif{
    constructor(){
        this.csrf = getCookieValue('csrftoken');
        this.mids = [];
        this.privacy();
    }
    privacy(){
        var $markup = $("<div><div class='enif_message enif_message_privacy'>" +
            "<span class='enif_message_text'>Zur Verbesserung unseres Services erheben wir personenbezogene Daten. Bitte bestätigen Sie, dass Sie damit einverstanden sind. Unsere Datenschutzbestimmungen können Sie hier einsehen: <a href='' >Datenschutz</a></span>" +
            "<span class='enif_privacy_accept'>Akzeptieren</span>" +
            "</div></div>");
        $('.enif_messages_div').append($markup);
        $(".enif_messages_div").scrollTop($(".enif_messages_div")[0].scrollHeight);
    }
    initiate(){
        let that = this
        $.ajax({
            type: 'POST',
            headers: { "X-CSRFToken": this.csrf },
            url: '/api/v1/session/',
            success: function (result, status, xhr) {
                that['Session'] = result['data']
                that.get();
            },
            error: function (result, status, xhr) {
                console.log(status)
                console.log(result)
            },
            timeout: 120000,
        });
    };
    extend_session(){
        let that = this;
        $.ajax({
            type: 'PUT',
            headers: { "X-CSRFToken": this.csrf },
            url: '/api/v1/session/' + this.Session.Token,
            success: function (result, status, xhr) {
                that['Session'] = result['data'];
            },
            error: function (result, status, xhr) {
                console.log(status)
                console.log(result)
            },
            timeout: 120000,
        });
    }
    check_session(){
        var now = new Date();
        var s_vu = new Date(this.Session.Valid_Until);
        if(now > s_vu){
            this.extend_session();
        };
    }
    get(){
        this.check_session();
        let that = this;
        $.ajax({
            type: 'GET',
            url: '/api/v1/enif/' + this.Session.Token,
            success: function (result, status, xhr) {
                that['Enif'] = result['Enif']
                that.render();
            },
            error: function (result, status, xhr) {
                console.log(status)
                console.log(result)
            },
            timeout: 120000,
        });
    }
    post(pattern, predict, user_feedback, intent = null) {
        this.check_session();
        let that = this;
        $('.enif_loader').removeClass('hide');
        $('.enif_messages_div').append(this.markup("User", pattern));
        $(".enif_messages_div").scrollTop($(".enif_messages_div")[0].scrollHeight);
        $.ajax({
            type: 'POST',
            headers: { "X-CSRFToken": this.csrf },
            data: { "Pattern": pattern, "Predict": predict, "Intent": intent, "User_Feedback": user_feedback},
            url: '/api/v1/request/' + this.Session.Token + "/",
            success: function (result, status, xhr) {
                that.get()
                $('.enif_loader').addClass('hide');
            },
            error: function (result, status, xhr) {
                console.log(status)
                console.log(result)
            },
            timeout: 120000,
        });
    }
    markup(type, text, timestamp=null){
        var $markup = $("<div><div class='enif_message'>" +
                        "<span class='enif_message_text'></span>" +
                        "<span class='enif_message_info'></span>" +
                        "<i class='fas fa-sort-down enif_message_arrow'></i>" +
                        "</div></div>");
        $markup.find('.enif_message_text').text(text);
        if(timestamp){
            var d = new Date(timestamp)
            var t = d.toLocaleTimeString();
        }else{
            var d = new Date()
            var t = d.toLocaleTimeString();
        }
        if(type=="Enif"){
            $markup.find('.enif_message').addClass('enif_reply');
            $markup.find('.enif_message_info').text("Enif - " + t);
        } else if (type == "User"){
            $markup.find('.enif_message').addClass('enif_question');
            $markup.find('.enif_message_info').text("Sie - " + t);
        }
        return $markup
    }
    render_options(options){
        var $wrapper = $("<div class='enif_options_wrapper'></div>");
        var $markup = null;
        for(var i in options){
            $markup = $("<div class='enif_option' data-intent_id=''>" +
                "<i class='enif_option_i'></i>" +
                "<span class='enif_options_text'></span>" +
                "</div>");
            $markup.find('i').addClass(options[i].Symbol)
            $markup.find('.enif_options_text').text(options[i].Text)
            $markup.find('.enif_option').attr("data-intent_id", options[i].Intent)
            console.log($markup)
            $wrapper.append($markup)
        }
        console.log($wrapper)
        return $wrapper
    }
    render(){
        for(var i in this.Enif.Messages){
            if (!this.mids.includes(this.Enif.Messages[i].ID || this.Enif.Messages[i].ID == null )){
                if (this.Enif.Messages[i].Source == "Enif" && this.Enif.Messages[i].Message_Type == "PlainText"){
                    $('.enif_messages_div').append(this.markup(this.Enif.Messages[i].Source, this.Enif.Messages[i].Text, this.Enif.Messages[i].Timestamp));
                    this.mids.push(this.Enif.Messages[i].ID);
                }
                if (this.Enif.Messages[i].Source == "Enif" && this.Enif.Messages[i].Message_Type == "Options") {
                    $('.enif_messages_div').append(this.render_options(this.Enif.Messages[i].Options));
                }
            }
        }
        $(".enif_messages_div").scrollTop($(".enif_messages_div")[0].scrollHeight);
        
    }
}
